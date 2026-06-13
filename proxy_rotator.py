from __future__ import annotations

import logging
import os
import random
import threading
import time
from typing import Dict, List, Optional

import requests


class ProxyRotator:
    def __init__(self, proxy_list: Optional[List[str]] = None, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("proxy_rotator")
        raw = proxy_list or [p.strip() for p in os.environ.get("PROXY_LIST", "").split(",") if p.strip()]
        self._proxies: List[str] = raw
        self._blacklist: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._blacklist_duration = 300

    @property
    def available(self) -> List[str]:
        now = time.monotonic()
        with self._lock:
            return [p for p in self._proxies if p not in self._blacklist or self._blacklist[p] < now]

    def add(self, proxy: str) -> None:
        with self._lock:
            if proxy not in self._proxies:
                self._proxies.append(proxy)

    def remove(self, proxy: str) -> None:
        with self._lock:
            if proxy in self._proxies:
                self._proxies.remove(proxy)
            self._blacklist.pop(proxy, None)

    def is_healthy(self, proxy: str, timeout: int = 10) -> bool:
        try:
            resp = requests.get(
                "http://httpbin.org/ip",
                proxies={"http": proxy, "https": proxy},
                timeout=timeout,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def get(self) -> Optional[str]:
        pool = self.available
        if not pool:
            if self.logger:
                self.logger.warning("No available proxies; clearing blacklist and retrying")
            with self._lock:
                self._blacklist.clear()
                pool = self._proxies[:]
        if not pool:
            return None
        random.shuffle(pool)
        candidate = pool[0]
        if self.is_healthy(candidate):
            return candidate
        self.mark_failed(candidate)
        return self.get() if self.available else None

    def mark_failed(self, proxy: str) -> None:
        with self._lock:
            self._blacklist[proxy] = time.monotonic() + self._blacklist_duration
        if self.logger:
            self.logger.info("Proxy %s blacklisted for %ds", proxy, self._blacklist_duration)

    def mark_success(self, proxy: str) -> None:
        pass

    @property
    def count(self) -> int:
        return len(self._proxies)
