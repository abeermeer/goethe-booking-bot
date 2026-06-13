from student_queue import StudentQueue


def test_enqueue_dequeue():
    q = StudentQueue()
    q.enqueue("Alice", "a@x.com", "A1", "Berlin")
    assert q.pending_count == 1
    item = q.dequeue()
    assert item is not None
    assert item["name"] == "Alice"
    assert q.active == item["id"]


def test_complete():
    q = StudentQueue()
    q.enqueue("Bob", "b@x.com", "A2", "Munich")
    item = q.dequeue()
    q.complete(item["id"])
    assert q.active is None
    summary = q.summary()
    assert summary["completed"] == 1


def test_fail():
    q = StudentQueue()
    q.enqueue("Charlie", "c@x.com", "B1", "Hamburg")
    item = q.dequeue()
    q.fail(item["id"])
    assert q.active is None
    summary = q.summary()
    assert summary["failed"] == 1


def test_priority_ordering():
    q = StudentQueue()
    q.enqueue("Low", "l@x.com", "A1", "Berlin", priority=0)
    q.enqueue("High", "h@x.com", "A1", "Berlin", priority=10)
    first = q.dequeue()
    assert first["name"] == "High"
    second = q.dequeue()
    assert second["name"] == "Low"


def test_empty_dequeue():
    q = StudentQueue()
    assert q.dequeue() is None


def test_clear():
    q = StudentQueue()
    q.enqueue("Diana", "d@x.com", "A1", "Cologne")
    q.clear()
    assert q.pending_count == 0


def test_summary():
    q = StudentQueue()
    q.enqueue("Eve", "e@x.com", "A1", "Berlin")
    assert q.summary()["total"] == 1
    assert q.summary()["pending"] == 1


def test_reset():
    q = StudentQueue()
    q.enqueue("Frank", "f@x.com", "A2", "Berlin")
    item = q.dequeue()
    q.reset(item["id"])
    assert q.active is None
    assert q.pending_count == 1
