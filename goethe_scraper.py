"""Scrape Goethe exam schedule from goethe.de for Pakistan cities.

Parses exam date blocks from the Goethe-Institut Pakistan registration page.
Caches results for 1 hour.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from typing import Dict, List
from urllib.request import urlopen, Request

CACHE_TTL = 3600
GOETHE_URL = "https://www.goethe.de/ins/pk/en/spr/prf/anm.html"

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9,     "october": 10, "november": 11, "december": 12,
    "januar": 1, "februar": 2, "märz": 3, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}

CITY_PATTERNS = [
    ("Karachi", r'Goethe-Institut\s+Karachi'),
    ("Lahore", r'Annemarie-Schimmel-Haus.*?Lahore'),
    ("Islamabad", r'(?:NUML|National University of Modern Languages).*?Islamabad'),
]


@dataclass
class ExamEntry:
    level: str
    city: str
    exam_date: str
    reg_open: str
    reg_open_time: str = ""
    url: str = GOETHE_URL


_last_cache: dict = {"data": None, "ts": 0}


def _fetch_html(url: str) -> str:
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _normalize_date(date_str: str) -> str:
    date_str = date_str.replace("\u2013", "-").replace("\u2014", "-").strip()
    m = re.match(r'(\d{1,2})[\.\-](\d{1,2})[\.\-](\d{4})', date_str)
    if m:
        return f"{m.group(1).zfill(2)}.{m.group(2).zfill(2)}.{m.group(3)}"
    m = re.match(r'(\d{1,2})\s+([A-Za-zäöü]+)\s+(\d{4})', date_str)
    if m:
        day, month_str, year = m.group(1), m.group(2).lower(), m.group(3)
        month = MONTHS.get(month_str)
        if month:
            return f"{day.zfill(2)}.{month:02d}.{year}"
    return date_str


def _detect_city(context: str) -> str | None:
    for city, pattern in CITY_PATTERNS:
        if re.search(pattern, context, re.IGNORECASE | re.DOTALL):
            return city
    return None


def _parse_schedule(html: str) -> List[ExamEntry]:
    levels_of_interest = {"A1", "A2", "B1"}
    all_blocks = list(re.finditer(r'<strong>(.*?)</strong>', html, re.DOTALL))

    # Filter to level-bearing blocks only, preserving their order
    level_blocks = []
    for m in all_blocks:
        block_levels = set(re.findall(r'\b([A-C]\d)\b', m.group(1)))
        if block_levels & levels_of_interest:
            level_blocks.append((m, block_levels))

    entries: List[ExamEntry] = []
    current_city = "Pakistan"

    for idx, (match, block_levels) in enumerate(level_blocks):
        inner = match.group(1)
        matching = block_levels & levels_of_interest

        # Detect city: look in the gap since the previous level block
        if idx == 0:
            prev_end = 0
        else:
            prev_end = level_blocks[idx - 1][0].end()
        ctx = html[prev_end:match.start()]
        detected = _detect_city(ctx)
        if detected:
            current_city = detected

        br_split = re.split(r'<br\s*/?>', inner, flags=re.IGNORECASE)
        if len(br_split) < 2:
            continue
        exam_date = _normalize_date(br_split[-1].strip())
        if not exam_date:
            continue

        block_end = match.end()
        if idx + 1 < len(level_blocks):
            end = level_blocks[idx + 1][0].start()
        else:
            end = len(html)
        between = html[block_end:end]

        reg_lines = re.findall(
            r'([A-C]\d(?:,\s*[A-C]\d)*)\s*:\s*from\s+(\d{1,2}\.\d{1,2}\.\d{4})\s+at\s+(\d{1,2}:\d{2})',
            between, re.IGNORECASE,
        )

        for levels_str, reg_date, reg_time in reg_lines:
            parsed_levels = re.findall(r'[A-C]\d', levels_str.upper())
            for lv in parsed_levels:
                if lv in levels_of_interest:
                    entries.append(ExamEntry(
                        level=lv,
                        city=current_city,
                        exam_date=exam_date,
                        reg_open=reg_date,
                        reg_open_time=reg_time,
                    ))

    seen = set()
    unique = []
    for e in entries:
        key = (e.level, e.city, e.exam_date, e.reg_open)
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
    except Exception as e:
        print(f"Scraper error: {e}")
        return _last_cache.get("data") or []


def to_dict(entries: List[ExamEntry]) -> List[Dict]:
    return [asdict(e) for e in entries]
