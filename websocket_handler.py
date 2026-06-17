"""WebSocket handler for real-time log streaming.

Provides a WebSocket endpoint that pushes booking logs to connected
clients in real time, replacing the current polling-based log viewer.

Usage:
  from websocket_handler import setup_websocket
  setup_websocket(app)  # attaches WebSocket routes to the Flask app

Dependencies (optional):
  - flask-sock: pip install flask-sock
  - Or use a standalone WebSocket server with gevent-websocket

TODO:
  - Add authentication for WebSocket connections
  - Add log filtering by student/level
  - Add reconnection handling
  - Add rate limiting
"""
from __future__ import annotations

import json
import queue
import threading
from typing import Set

LOG_QUEUE: queue.Queue = queue.Queue()
_clients: Set = set()
_lock = threading.Lock()


class LogBroadcaster:
    """Collects logs from various sources and broadcasts to WebSocket clients."""

    def __init__(self):
        self._running = False
        self._thread: threading.Thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def push(self, log_entry: dict):
        LOG_QUEUE.put(log_entry)

    def register(self, client):
        with _lock:
            _clients.add(client)

    def unregister(self, client):
        with _lock:
            _clients.discard(client)

    def _loop(self):
        while self._running:
            try:
                entry = LOG_QUEUE.get(timeout=1)
                payload = json.dumps(entry)
                with _lock:
                    dead = set()
                    for client in _clients:
                        try:
                            client.send(payload)
                        except Exception:
                            dead.add(client)
                    _clients -= dead
            except queue.Empty:
                continue


# Singleton
broadcaster = LogBroadcaster()


def setup_websocket(app):
    """Attach WebSocket routes to a Flask app (requires flask-sock)."""
    try:
        from flask_sock import Sock
        sock = Sock(app)

        @sock.route("/ws/logs")
        def logs_ws(ws):
            broadcaster.register(ws)
            try:
                while True:
                    ws.receive(timeout=30)  # keep alive
            except Exception:
                pass
            finally:
                broadcaster.unregister(ws)
    except ImportError:
        # flask-sock not installed — logs will use polling
        pass
