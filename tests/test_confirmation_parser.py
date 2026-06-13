from confirmation_parser import (
    parse_confirmation_text,
    parse_confirmation_url,
    summarize,
)


def test_parse_confirmation_reference():
    text = "Your booking confirmation number: ABC123XYZ. Thank you for registering."
    r = parse_confirmation_text(text)
    assert r["reference"] == "ABC123XYZ"
    assert r["status"] == "confirmed"


def test_parse_confirmation_german():
    text = "Ihre Buchungsbestätigung: Referenznummer DEF456GHI. Sie sind erfolgreich angemeldet."
    r = parse_confirmation_text(text)
    assert r["reference"] == "DEF456GHI"
    assert r["status"] == "confirmed"


def test_parse_exam_date():
    text = "Exam date: 15.07.2026 at 09:00. Booking reference: REF001."
    r = parse_confirmation_text(text)
    assert r["reference"] == "REF001"
    assert r["exam_date"] == "2026-07-15"
    assert r["exam_time"] == "09:00"


def test_parse_level():
    text = "Your B1 exam has been confirmed. Reference: B1REF123."
    r = parse_confirmation_text(text)
    assert r["exam_level"] == "B1"


def test_parse_city():
    text = "Location: Berlin. Reference: BER001."
    r = parse_confirmation_text(text)
    assert r["exam_city"] == "Berlin"


def test_parse_error_slot_full():
    text = "Error: No available slots for this exam. Please try again later."
    r = parse_confirmation_text(text)
    assert r["status"] == "error"
    assert r["errors"] is not None


def test_parse_error_timeout():
    text = "The connection timed out. Please try again."
    r = parse_confirmation_text(text)
    assert r["status"] == "error"


def test_parse_unknown():
    text = "Some random page content with no booking info."
    r = parse_confirmation_text(text)
    assert r["status"] == "unknown"
    assert r["reference"] is None


def test_parse_url_with_ref():
    url = "https://mein.goethe.de/booking?confirmation=XYZ789"
    r = parse_confirmation_url(url)
    assert r["booking_reference_url"] == "XYZ789"


def test_parse_url_goethe():
    url = "https://mein.goethe.de/some/page"
    r = parse_confirmation_url(url)
    assert r["is_goethe_page"] is True


def test_summary():
    r = {"status": "confirmed", "reference": "ABC123", "exam_level": "A1", "exam_city": "Berlin", "exam_date": "2026-07-15", "errors": None}
    s = summarize(r)
    assert "Status: confirmed" in s
    assert "Ref: ABC123" in s
    assert "Level: A1" in s
