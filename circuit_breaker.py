from __future__ import annotations

import logging
import threading
import time
from typing import Optional


class CircuitBreaker:
    """Prevents hammering a down site.

    States:
      closed   — normal operation, requests allowed
      open     — N consecutive failures tripped; requests blocked for cooldown
      half-open — cooldown expired; one probe request allowed

    Thread-safe.
    """

    def __init__(self, threshold: int = 10, cooldown: float = 900.0,
                 logger: Optional[logging.Logger] = None):
        self.threshold = threshold
        self.cooldown = cooldown
        self._lock = threading.Lock()
        self._consecutive_failures = 0
        self._open_until: float = 0.0  # monotonic time
        self._logger = logger or logging.getLogger("circuit_breaker")
        self._state = "closed"

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def consecutive_failures(self) -> int:
        with self._lock:
            return self._consecutive_failures

    def allow_request(self) -> bool:
        """Whether a request to the upstream should be allowed now."""
        with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if time.monotonic() >= self._open_until:
                    self._state = "half-open"
                    self._logger.info("Circuit breaker → half-open (cooldown expired)")
                    return True
                return False
            # half-open: allow exactly one probe
            return True

    def record_failure(self):
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.threshold:
                was_open = self._state == "open"
                self._state = "open"
                self._open_until = time.monotonic() + self.cooldown
                if not was_open:
                    self._logger.warning(
                        "Circuit breaker → OPEN after %d failures (cooldown %.0fs)",
                        self._consecutive_failures, self.cooldown,
                    )

    def record_success(self):
        with self._lock:
            if self._state == "half-open":
                self._logger.info("Circuit breaker → closed (probe succeeded)")
            self._state = "closed"
            self._consecutive_failures = 0
            self._open_until = 0.0

    def wait_until_allowed(self, poll: float = 5.0, stop_event: Optional[threading.Event] = None) -> bool:
        """Block caller until the breaker allows a request. Returns False if stop_event fires."""
        while not self.allow_request():
            remaining = max(0, self._open_until - time.monotonic())
            self._logger.info("Circuit breaker open — waiting %.0fs more", remaining)
            gap = min(poll, remaining) if remaining > 0 else poll
            if stop_event:
                if stop_event.wait(gap):
                    return False
            else:
                time.sleep(gap)
        return True

    def reset(self):
        with self._lock:
            self._state = "closed"
            self._consecutive_failures = 0
            self._open_until = 0.0
