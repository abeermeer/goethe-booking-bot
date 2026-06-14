from __future__ import annotations

import logging
import threading
import time
from typing import Optional


class DeadManSwitch:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("deadman")
        self._last_heartbeat: float = time.monotonic()
        self._lock = threading.Lock()
        self._alive = True
        self._timeout_secs = 300
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

    def ping(self) -> None:
        with self._lock:
            self._last_heartbeat = time.monotonic()
            self._alive = True

    @property
    def is_alive(self) -> bool:
        with self._lock:
            return self._alive

    def check(self) -> bool:
        with self._lock:
            elapsed = time.monotonic() - self._last_heartbeat
            if elapsed > self._timeout_secs and self._alive:
                self._alive = False
                if self.logger:
                    self.logger.warning(
                        "Dead man switch triggered — no heartbeat for %.0fs",
                        elapsed,
                    )
                return False
            return self._alive

    @property
    def seconds_since_ping(self) -> float:
        with self._lock:
            return time.monotonic() - self._last_heartbeat

    def start_monitor(self, interval: int = 60, on_death: Optional[callable] = None) -> threading.Thread:
        self._stop_event.clear()
        def _loop():
            while not self._stop_event.is_set():
                if self._stop_event.wait(timeout=interval):
                    break
                if not self.check():
                    if on_death:
                        try:
                            on_death()
                        except Exception as exc:
                            if self.logger:
                                self.logger.exception("Dead man callback failed: %s", exc)
                    break

        self._monitor_thread = threading.Thread(target=_loop, daemon=True)
        self._monitor_thread.start()
        return self._monitor_thread

    def stop_monitor(self) -> None:
        self._stop_event.set()
