import json
from deadman import DeadManSwitch
from student_queue import StudentQueue
from confirmation_parser import parse_confirmation_text, summarize
import db


def test_deadman_and_notifications():
    d = DeadManSwitch()
    d.ping()
    assert d.is_alive is True
    assert d.seconds_since_ping < 1.0


def test_queue_and_db_roundtrip():
    q = StudentQueue()
    q.enqueue("Alice", "a@x.com", "A1", "Berlin")
    q.enqueue("Bob", "b@x.com", "A2", "Munich")
    items = db.get_queue()
    assert len(items) == 2
    item = q.dequeue()
    assert item["name"] == "Alice"
    q.complete(item["id"])
    db_items = db.get_queue()
    completed = [i for i in db_items if i["status"] == "completed"]
    assert len(completed) == 1


def test_confirmation_parser_integration():
    text = "Your booking confirmation: REF12345. Exam: B1. Location: Berlin on 15.07.2026. Thank you!"
    parsed = parse_confirmation_text(text)
    assert parsed["reference"] == "REF12345"
    assert parsed["exam_level"] == "B1"
    assert parsed["exam_city"] == "Berlin"
    assert parsed["exam_date"] == "2026-07-15"
    assert parsed["status"] == "confirmed"

    summary = summarize(parsed)
    assert "Status: confirmed" in summary
    assert "Ref: REF12345" in summary


def test_student_db_persistence():
    students = [
        {"name": "TestUser", "email": "test@x.com", "level": "A1", "city": "Karachi", "booking_datetime": "2026-07-17T09:00"},
    ]
    db.save_students(students)
    loaded = db.get_students()
    assert len(loaded) >= 1
    found = [s for s in loaded if s["name"] == "TestUser"]
    assert len(found) == 1
    assert found[0]["level"] == "A1"
