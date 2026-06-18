from __future__ import annotations

import json
import logging
import threading
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

POLL_TIMEOUT = 30
POLL_INTERVAL = 2


class TelegramCommander:
    def __init__(
        self,
        token: str,
        allowed_chat_id: str,
        bot_ref: Any,
        logger: Optional[logging.Logger] = None,
    ):
        self.token = token
        self.allowed_chat_id = self._parse_chat_id(allowed_chat_id)
        self.bot_ref = bot_ref
        self.logger = logger or logging.getLogger("telegram_cmd")
        self._offset = 0
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._reply = _ReplySender(token)
        self._notify_enabled = True

    def _parse_chat_id(self, raw: str) -> Optional[int]:
        try:
            return int(raw.strip())
        except (ValueError, AttributeError):
            return None

    def _get_updates(self) -> List[Dict]:
        params = {"offset": self._offset, "timeout": POLL_TIMEOUT}
        url = f"https://api.telegram.org/bot{self.token}/getUpdates?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=POLL_TIMEOUT + 5) as resp:
                data = json.loads(resp.read().decode())
            return data.get("result", [])
        except Exception as exc:
            self.logger.debug("getUpdates error: %s", exc)
            return []

    def _handle_update(self, update: Dict):
        msg = update.get("message") or update.get("edited_message") or {}
        chat_id = msg.get("chat", {}).get("id")
        if self.allowed_chat_id is None or chat_id != self.allowed_chat_id:
            return
        text = (msg.get("text") or "").strip()
        if not text.startswith("/"):
            return
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        self.logger.info("Telegram command: %s args=%s", cmd, args)
        method_name = COMMAND_MAP.get(cmd)
        if method_name:
            handler = getattr(self, method_name, None)
            if handler:
                try:
                    handler(args)
                except Exception as exc:
                    self.logger.exception("Command %s failed: %s", cmd, exc)
                    self._reply.send(chat_id, f"Error: {exc}")
        else:
            self._reply.send(chat_id, f"Unknown command: {cmd}\n/help for available commands")

    def _run(self):
        self.logger.info("Telegram commander polling started")
        while not self._stop.is_set():
            updates = self._get_updates()
            for update in updates:
                self._offset = update["update_id"] + 1
                self._handle_update(update)
            for _ in range(POLL_INTERVAL):
                if self._stop.is_set():
                    break
                time.sleep(0.5)

    def start(self):
        if self._thread and self._thread.is_alive():
            self.logger.warning("Telegram commander already running")
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.logger.info("Telegram commander stopped")

    def send(self, message: str):
        if self._notify_enabled and self.allowed_chat_id:
            self._reply.send(self.allowed_chat_id, message)

    # ── Command handlers ──

    def cmd_start(self, args: str):
        ref = self.bot_ref
        if hasattr(ref, "start_bot_from_telegram"):
            ref.start_bot_from_telegram()
            self._reply.send(self.allowed_chat_id, "Bot started. Waiting for booking time.")
        else:
            self._reply.send(self.allowed_chat_id, "Bot cannot be started via Telegram (no start function)")

    def cmd_stop(self, args: str):
        ref = self.bot_ref
        if args:
            name = args.strip()
            if hasattr(ref, "stop_student"):
                ref.stop_student(name)
                self._reply.send(self.allowed_chat_id, f"Stopped: {name}")
            else:
                self._reply.send(self.allowed_chat_id, "Cannot stop individual student")
        else:
            if hasattr(ref, "stop_all"):
                ref.stop_all()
                self._reply.send(self.allowed_chat_id, "All students stopped.")
            else:
                self._reply.send(self.allowed_chat_id, "Stop all not available")

    def cmd_status(self, args: str):
        ref = self.bot_ref
        running = getattr(ref, "bot_running", False)
        statuses = getattr(ref, "student_status", {})
        results = getattr(ref, "student_results", [])
        lines = [f"Bot running: {'Yes' if running else 'No'}"]
        if statuses:
            for key, info in statuses.items():
                lines.append(f"  {key}: {info.get('status', '?')} - {info.get('details', '')}")
        if results:
            lines.append(f"Results: {len(results)} total")
            for r in results[-3:]:
                lines.append(f"  {r.get('name')}: {r.get('status')} ref={r.get('reference', 'N/A')}")
        else:
            lines.append("No results yet")
        self._reply.send(self.allowed_chat_id, "\n".join(lines))

    def cmd_schedule(self, args: str):
        try:
            import booking_helper as bh
            sched = bh.get_schedule()
            if not sched:
                self._reply.send(self.allowed_chat_id, "No schedule data available")
                return
            lines = ["Exam Schedule:"]
            for entry in sched[:10]:
                level = entry.get("level", getattr(entry, "level", "?"))
                city = entry.get("city", getattr(entry, "city", "?"))
                exam_date = entry.get("exam_date", getattr(entry, "exam_date", "?"))
                reg_open = entry.get("reg_open", getattr(entry, "reg_open", "?"))
                lines.append(f"  {level} | {city} | {exam_date} | Reg: {reg_open}")
            if len(sched) > 10:
                lines.append(f"  ... and {len(sched) - 10} more")
            self._reply.send(self.allowed_chat_id, "\n".join(lines))
        except Exception as exc:
            self._reply.send(self.allowed_chat_id, f"Schedule error: {exc}")

    def cmd_check(self, args: str):
        if not args:
            self._reply.send(self.allowed_chat_id, "Usage: /check A1 Karachi")
            return
        parts = args.rsplit(maxsplit=1)
        if len(parts) != 2:
            self._reply.send(self.allowed_chat_id, "Usage: /check A1 Karachi")
            return
        level, city = parts[0].upper(), parts[1]
        ref = self.bot_ref
        if hasattr(ref, "check_slot"):
            try:
                result = ref.check_slot(level, city)
                if result:
                    self._reply.send(self.allowed_chat_id, f"{level} {city}: Slot available!")
                else:
                    self._reply.send(self.allowed_chat_id, f"{level} {city}: No slot found")
            except Exception as exc:
                self._reply.send(self.allowed_chat_id, f"Check error: {exc}")
        else:
            self._reply.send(self.allowed_chat_id, "Slot check not available")

    def cmd_history(self, args: str):
        import db as _db
        try:
            q = args.strip() if args else None
            if q:
                entries = _db.search_logs(q, limit=10)
            else:
                results = getattr(self.bot_ref, "student_results", [])
                if results:
                    lines = ["Recent results:"]
                    for r in results[-10:]:
                        lines.append(f"  {r.get('name')}: {r.get('status')} ref={r.get('reference', 'N/A')}")
                    self._reply.send(self.allowed_chat_id, "\n".join(lines))
                    return
                entries = _db.get_recent_logs(limit=10)
            if not entries:
                self._reply.send(self.allowed_chat_id, "No history found")
                return
            lines = [f"History (last {len(entries)}):"]
            for e in entries[-10:]:
                lines.append(f"  {e.get('time', '')[:19]} {e.get('level', '')}: {e.get('message', '')[:100]}")
            self._reply.send(self.allowed_chat_id, "\n".join(lines))
        except Exception as exc:
            self._reply.send(self.allowed_chat_id, f"History error: {exc}")

    def cmd_restart(self, args: str):
        ref = self.bot_ref
        if hasattr(ref, "restart_bot"):
            self._reply.send(self.allowed_chat_id, "Restarting bot...")
            ref.restart_bot()
        else:
            self._reply.send(self.allowed_chat_id, "Restart not available")

    def cmd_notify(self, args: str):
        val = args.strip().lower()
        if val in ("on", "true", "1", "yes"):
            self._notify_enabled = True
            self._reply.send(self.allowed_chat_id, "Notifications enabled")
        elif val in ("off", "false", "0", "no"):
            self._notify_enabled = False
            self._reply.send(self.allowed_chat_id, "Notifications disabled")
        else:
            self._reply.send(self.allowed_chat_id, f"Notifications: {'ON' if self._notify_enabled else 'OFF'}")

    def cmd_help(self, args: str):
        help_text = (
            "/start - Start booking for all loaded students\n"
            "/stop [name] - Stop specific student (or all)\n"
            "/stopall - Stop all students\n"
            "/status - Current bot status\n"
            "/schedule - Show upcoming exams\n"
            "/check A1 Karachi - Check slot availability\n"
            "/history [query] - Recent bookings/logs\n"
            "/restart - Restart the bot\n"
            "/notify on/off - Toggle notifications\n"
            "/help - This menu"
        )
        self._reply.send(self.allowed_chat_id, help_text)


class _ReplySender:
    def __init__(self, token: str):
        self.token = token

    def send(self, chat_id: int, text: str):
        if not chat_id or not self.token:
            return
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": str(chat_id),
                "text": text[:4000],
                "parse_mode": "HTML",
            }).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            urllib.request.urlopen(req, timeout=10)
        except Exception as exc:
            logging.getLogger("telegram_cmd").debug("Reply send failed: %s", exc)


COMMAND_MAP: Dict[str, str] = {}

for _name in dir(TelegramCommander):
    if _name.startswith("cmd_"):
        cmd = "/" + _name.replace("cmd_", "")
        COMMAND_MAP[cmd] = _name

# Aliases
COMMAND_MAP["/stopall"] = "cmd_stop"
