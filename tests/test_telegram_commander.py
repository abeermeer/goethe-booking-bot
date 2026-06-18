import threading
import time
from unittest.mock import MagicMock

from telegram_commander import TelegramCommander


class FakeBotRef:
    bot_running = False
    student_status = {}
    student_results = []

    def start_bot_from_telegram(self):
        self.bot_running = True
        self.student_status["test|A1|Karachi"] = {"status": "Started", "color": "info", "details": ""}

    def stop_all(self):
        self.bot_running = False

    def check_slot(self, level, city):
        return level == "A1" and city == "Karachi"

    def restart_bot(self):
        self.stop_all()
        self.start_bot_from_telegram()


def _text_sent(c):
    return c._reply.send.call_args[0][1]


def test_cmder_parses_chat_id():
    c = TelegramCommander("token", "12345", None)
    assert c.allowed_chat_id == 12345


def test_cmder_handles_bad_chat_id():
    c = TelegramCommander("token", "", None)
    assert c.allowed_chat_id is None


def test_cmd_start_calls_bridge():
    ref = FakeBotRef()
    c = TelegramCommander("token", "1", ref)
    c._reply.send = MagicMock()
    c.cmd_start("")
    assert ref.bot_running is True


def test_cmd_stop_calls_bridge():
    ref = FakeBotRef()
    ref.bot_running = True
    c = TelegramCommander("token", "1", ref)
    c._reply.send = MagicMock()
    c.cmd_stop("")
    assert ref.bot_running is False


def test_cmd_status_shows_state():
    ref = FakeBotRef()
    ref.bot_running = True
    ref.student_status["test|A1|Karachi"] = {"status": "Confirmed!", "color": "success", "details": "Ref: ABC"}
    c = TelegramCommander("token", "1", ref)
    c._reply.send = MagicMock()
    c.cmd_status("")
    sent = _text_sent(c)
    assert "Yes" in sent
    assert "test|A1|Karachi" in sent


def test_cmd_check_usage():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c.cmd_check("")
    assert "Usage" in _text_sent(c)


def test_cmd_check_missing_city():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c.cmd_check("A1")
    assert "Usage" in _text_sent(c)


def test_cmd_check_found():
    ref = FakeBotRef()
    c = TelegramCommander("token", "1", ref)
    c._reply.send = MagicMock()
    c.cmd_check("A1 Karachi")
    sent = _text_sent(c)
    assert "available" in sent.lower()


def test_cmd_check_not_found():
    ref = FakeBotRef()
    c = TelegramCommander("token", "1", ref)
    c._reply.send = MagicMock()
    c.cmd_check("B2 Lahore")
    sent = _text_sent(c)
    assert "No slot" in sent


def test_cmd_notify_toggle():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    assert c._notify_enabled is True
    c.cmd_notify("off")
    assert c._notify_enabled is False
    c.cmd_notify("on")
    assert c._notify_enabled is True


def test_cmd_notify_status():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c.cmd_notify("")
    sent = _text_sent(c)
    assert "ON" in sent or "OFF" in sent


def test_send_honors_notify_flag():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c._notify_enabled = False
    c.send("test")
    c._reply.send.assert_not_called()
    c._notify_enabled = True
    c.send("test")
    c._reply.send.assert_called_once()


def test_help_includes_commands():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c.cmd_help("")
    sent = _text_sent(c)
    for cmd in ["/start", "/stop", "/status", "/check", "/help"]:
        assert cmd in sent


def test_cmd_restart():
    ref = FakeBotRef()
    c = TelegramCommander("token", "1", ref)
    c._reply.send = MagicMock()
    c.cmd_restart("")
    assert ref.bot_running is True


def test_unknown_command():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c._handle_update({
        "update_id": 1,
        "message": {"chat": {"id": 1}, "text": "/invalid_command"}
    })
    sent = _text_sent(c)
    assert "Unknown" in sent


def test_unauthed_chat_ignored():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c._handle_update({
        "update_id": 1,
        "message": {"chat": {"id": 999}, "text": "/start"}
    })
    c._reply.send.assert_not_called()


def test_csv_document_rejected_non_csv():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c._handle_update({
        "update_id": 1,
        "message": {"chat": {"id": 1}, "document": {"file_name": "photo.jpg", "file_id": "abc123", "file_size": 1000}}
    })
    sent = _text_sent(c)
    assert ".csv" in sent.lower() or "CSV" in sent


def test_csv_document_no_load_config_csv():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c._handle_update({
        "update_id": 1,
        "message": {"chat": {"id": 1}, "document": {"file_name": "students.csv", "file_id": "abc123", "file_size": 1000}}
    })
    # Should say config handler not available since FakeBotRef has no load_config_csv
    sent = _text_sent(c)
    assert "download" in sent.lower() or "Cannot" in sent or "config" in sent.lower()


def test_csv_document_oversized():
    c = TelegramCommander("token", "1", FakeBotRef())
    c._reply.send = MagicMock()
    c._handle_update({
        "update_id": 1,
        "message": {"chat": {"id": 1}, "document": {"file_name": "students.csv", "file_id": "abc123", "file_size": 600 * 1024}}
    })
    sent = _text_sent(c)
    assert "large" in sent.lower() or "500KB" in sent


def test_command_map_has_all_handlers():
    from telegram_commander import COMMAND_MAP
    expected = {"/start", "/stop", "/status", "/schedule", "/check", "/history", "/restart", "/notify", "/help", "/stopall"}
    assert set(COMMAND_MAP.keys()) == expected
