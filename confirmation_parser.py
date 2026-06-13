from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Pattern


CONFIRMATION_PATTERNS: List[Pattern] = [
    re.compile(r"(?:booking|reference|confirmation|registration|buchungs|referenz)\s*(?:number|no|id|code|ref|nummer)?\s*[:#]?\s*((?=[A-Z0-9\-]*[0-9])[A-Z0-9\-]{6,50})", re.IGNORECASE),
    re.compile(r"(?:PTN|Buchungs|Referenz)[:\s]*((?=[A-Z0-9\-]*[0-9])[A-Z0-9\-]{6,50})", re.IGNORECASE),
]

DATE_PATTERNS: List[Pattern] = [
    re.compile(r"(\d{1,2}[./]\d{1,2}[./]\d{2,4})\s*(?:at|um|,)?\s*(\d{1,2}[:.]\d{2})", re.IGNORECASE),
    re.compile(r"(?:exam|prüfung|test|examination)\s*(?:date|day|datum|am)?\s*[:#]?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})", re.IGNORECASE),
    re.compile(r"(?:date|datum)[:\s]+(\d{1,2}[./]\d{1,2}[./]\d{2,4})", re.IGNORECASE),
]

LEVEL_PATTERNS: List[Pattern] = [
    re.compile(r"\b(A1|A2|B1|B2|C1|C2)\b", re.IGNORECASE),
]

CITY_PATTERNS: List[Pattern] = [
    re.compile(r"(?:location|standort|city|stadt|place|ort)[:\s]+(\w[\w\s\-]+)", re.IGNORECASE),
]

ERROR_PATTERNS: List[Pattern] = [
    re.compile(r"(?:error|fehler|failed|gescheitert|not.?available|nicht.?verfügbar)", re.IGNORECASE),
    re.compile(r"(?:timed?\s*out|time.?out|timeout|abgelaufen)", re.IGNORECASE),
    re.compile(r"(?:already.?booked|bereits.?gebucht)", re.IGNORECASE),
    re.compile(r"(?:slot.?full|platz.?voll|no.?slots|keine.?plätze)", re.IGNORECASE),
    re.compile(r"(?:max.?participants|maximale.?teilnehmerzahl)", re.IGNORECASE),
]

SUCCESS_KEYWORDS: List[str] = [
    "thank you", "confirmation", "successful", "erfolgreich",
    "bestätigung", "booked", "gebucht", "confirmed", "registered",
    "angemeldet", "reservation", "reservierung",
]


def parse_confirmation_text(text: str) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {
        "reference": None,
        "exam_date": None,
        "exam_time": None,
        "exam_level": None,
        "exam_city": None,
        "errors": None,
        "status": "unknown",
    }

    for pattern in CONFIRMATION_PATTERNS:
        match = pattern.search(text)
        if match:
            result["reference"] = match.group(1).strip()
            break

    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            date_str = match.group(1).strip()
            try:
                for fmt in ["%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%d/%m/%y", "%m.%d.%Y", "%m/%d/%Y"]:
                    try:
                        parsed = datetime.strptime(date_str, fmt)
                        result["exam_date"] = parsed.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
            except Exception:
                result["exam_date"] = date_str
            if match.lastindex and match.lastindex >= 2:
                time_str = match.group(2).strip().replace(".", ":")
                result["exam_time"] = time_str
            break

    for pattern in LEVEL_PATTERNS:
        match = pattern.search(text)
        if match:
            result["exam_level"] = match.group(1).upper()
            break

    for pattern in CITY_PATTERNS:
        match = pattern.search(text)
        if match:
            result["exam_city"] = match.group(1).strip()
            break

    for pattern in ERROR_PATTERNS:
        match = pattern.search(text)
        if match:
            result["errors"] = match.group(0).strip()
            result["status"] = "error"
            break

    if result["status"] != "error":
        lower = text.lower()
        score = sum(1 for kw in SUCCESS_KEYWORDS if kw in lower)
        if score >= 2:
            result["status"] = "confirmed"
        elif score >= 1:
            result["status"] = "submitted"
        else:
            result["status"] = "unknown"

    return result


def parse_confirmation_url(url: str) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {
        "booking_reference_url": None,
        "is_goethe_page": False,
    }
    if "goethe" in url.lower():
        result["is_goethe_page"] = True
    ref_match = re.search(r"(?:booking|ref|id|confirmation)=([A-Za-z0-9\-]+)", url, re.IGNORECASE)
    if ref_match:
        result["booking_reference_url"] = ref_match.group(1)
    return result


def summarize(result: Dict[str, Optional[str]]) -> str:
    parts = [f"Status: {result.get('status', '?')}"]
    if result.get("reference"):
        parts.append(f"Ref: {result['reference']}")
    if result.get("exam_level"):
        parts.append(f"Level: {result['exam_level']}")
    if result.get("exam_city"):
        parts.append(f"City: {result['exam_city']}")
    if result.get("exam_date"):
        parts.append(f"Date: {result['exam_date']}")
    if result.get("errors"):
        parts.append(f"Error: {result['errors']}")
    return " | ".join(parts)
