from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

import db


class StudentQueue:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("queue")
        self._lock = threading.Lock()
        self._active: Optional[int] = None

    def enqueue(self, name: str, email: str, level: str, city: str, priority: int = 0) -> int:
        with self._lock:
            db.add_to_queue(name, email, level, city, priority)
            item = db.get_queue(status="pending")[-1]
            item_id = item["id"]
            if self.logger:
                self.logger.info("Enqueued %s (id=%d, priority=%d)", name, item_id, priority)
            return item_id

    def enqueue_many(self, students: List[Dict[str, Any]], default_priority: int = 0) -> None:
        for s in students:
            self.enqueue(
                s.get("name", ""),
                s.get("email", ""),
                s.get("level", ""),
                s.get("city", ""),
                priority=s.get("priority", default_priority),
            )

    def dequeue(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            pending = db.get_queue(status="pending")
            if not pending:
                return None
            item = pending[0]
            db.update_queue_item(item["id"], "in_progress")
            self._active = item["id"]
            if self.logger:
                self.logger.info("Dequeued %s (id=%d)", item["name"], item["id"])
            return item

    def complete(self, item_id: int, result: Optional[Dict] = None) -> None:
        with self._lock:
            db.update_queue_item(item_id, "completed", result)
            if self._active == item_id:
                self._active = None
            if self.logger:
                self.logger.info("Completed queue item %d", item_id)

    def fail(self, item_id: int, result: Optional[Dict] = None) -> None:
        with self._lock:
            db.update_queue_item(item_id, "failed", result)
            if self._active == item_id:
                self._active = None
            if self.logger:
                self.logger.warning("Failed queue item %d", item_id)

    def reset(self, item_id: int) -> None:
        with self._lock:
            db.update_queue_item(item_id, "pending")
            if self._active == item_id:
                self._active = None
            if self.logger:
                self.logger.info("Reset queue item %d to pending", item_id)

    @property
    def active(self) -> Optional[int]:
        return self._active

    @property
    def pending_count(self) -> int:
        return len(db.get_queue(status="pending"))

    @property
    def all(self) -> List[Dict[str, Any]]:
        return db.get_queue()

    def clear(self) -> None:
        with self._lock:
            db.clear_queue()
            self._active = None
            if self.logger:
                self.logger.info("Queue cleared")

    def summary(self) -> Dict[str, Any]:
        items = db.get_queue()
        return {
            "total": len(items),
            "pending": sum(1 for i in items if i["status"] == "pending"),
            "in_progress": sum(1 for i in items if i["status"] == "in_progress"),
            "completed": sum(1 for i in items if i["status"] == "completed"),
            "failed": sum(1 for i in items if i["status"] == "failed"),
            "active_id": self._active,
        }
