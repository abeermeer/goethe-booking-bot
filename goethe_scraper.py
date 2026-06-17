"""Scrape Goethe exam schedule (A1, A2, B1) from goethe.de.

Caches results for 1 hour to avoid hammering the site.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from urllib.request import urlopen, Request

CACHE_TTL = 3600  # 1 hour
GOETHE_URL = "https://www.goethe.de/ins/pk/en/spr/prf/anm.html"


@dataclass
class ExamEntry:
    level: str
    city: str
    date: str
    fee: str = ""
    url: str = ""


_last_cache: dict = {"data": None, "ts": 0}


def _fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_schedule(html: str) -> List[ExamEntry]:
    """Parse Goethe exam schedule HTML into structured entries."""
    entries: List[ExamEntry] = []
    levels = {"A1", "A2", "B1"}

    # Try to find exam tables/sections
    # Goethe uses various patterns — match level + city + date combinations
    for level in levels:
        # Find sections containing the level name
        pattern = re.compile(
            rf'{re.escape(level)}.*?(?:Karachi|Lahore|Islamabad|Faisalabad|Multan|Rawalpindi|Peshawar|Quetta|Hyderabad)',
            re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(html):
            snippet = match.group()
            city_match = re.search(
                r'(Karachi|Lahore|Islamabad|Faisalabad|Multan|Rawalpindi|Peshawar|Quetta|Hyderabad)',
                snippet, re.IGNORECASE,
            )
            date_match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4}|\d{4}-\d{2}-\d{2})', snippet)
            if city_match and date_match:
                entries.append(ExamEntry(
                    level=level.upper(),
                    city=city_match.group(1),
                    date=date_match.group(1),
                    url=GOETHE_URL,
                ))

    # Deduplicate
    seen = set()
    unique = []
    for e in entries:
        key = (e.level, e.city, e.date)
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def get_schedule(force_refresh: bool = False) -> List[ExamEntry]:
    now = time.time()
    if not force_refresh and _last_cache["data"] and (now - _last_cache["ts"]) < CACHE_TTL:
        return _last_cache["data"]

    try:
        html = _fetch_html(GOETHE_URL)
        entries = _parse_schedule(html)
        if entries:
            _last_cache["data"] = entries
            _last_cache["ts"] = now
        return entries or _last_cache.get("data") or []
    except Exception:
        return _last_cache.get("data") or []


def to_dict(entries: List[ExamEntry]) -> List[Dict]:
    return [asdict(e) for e in entries]
