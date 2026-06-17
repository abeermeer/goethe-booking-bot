"""Async worker for background booking processing.

The booking bot currently runs synchronously in a thread. This module
provides the hooks for an async worker that processes bookings in the
background using a job queue (Redis/Celery or similar).

Usage:
  from async_worker import BookingWorker
  worker = BookingWorker()
  worker.start()  # starts the worker loop
  worker.enqueue(student_data)
  worker.stop()

TODO:
  - Integrate with Redis for persistent queue
  - Add Celery or RQ backend for distributed processing
  - Add progress tracking and status updates
"""
from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class BookingJob:
    id: str
    student: Dict
    status: str = "pending"  # pending, running, done, failed
    result: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class BookingWorker:
    def __init__(self, max_workers: int = 1):
        self.max_workers = max_workers
        self._job_queue: queue.Queue[BookingJob] = queue.Queue()
        self._results: Dict[str, BookingJob] = {}
        self._stop = threading.Event()
        self._threads: List[threading.Thread] = []
        self._on_complete: Optional[Callable] = None

    def start(self):
        for _ in range(self.max_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        self._stop.set()

    def enqueue(self, student: Dict) -> str:
        job = BookingJob(
            id=f"job_{int(time.time() * 1000)}_{id(student)}",
            student=student,
        )
        self._job_queue.put(job)
        self._results[job.id] = job
        return job.id

    def get_result(self, job_id: str) -> Optional[BookingJob]:
        return self._results.get(job_id)

    def get_status(self, job_id: str) -> Optional[str]:
        job = self._results.get(job_id)
        return job.status if job else None

    def on_complete(self, callback: Callable):
        self._on_complete = callback

    def _worker_loop(self):
        while not self._stop.is_set():
            try:
                job = self._job_queue.get(timeout=1)
            except queue.Empty:
                continue
            job.status = "running"
            try:
                result = self._process(job.student)
                job.status = "done" if result.get("ok") else "failed"
                job.result = result
            except Exception as e:
                job.status = "failed"
                job.result = {"error": str(e)}
            self._results[job.id] = job
            if self._on_complete:
                self._on_complete(job)

    def _process(self, student: Dict) -> Dict:
        """Override this in subclasses to implement booking logic."""
        raise NotImplementedError
