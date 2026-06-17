"""Plugin manager — extensible booking pipeline.

Allows third-party plugins to hook into the booking lifecycle:
  - before_booking(student) → modify student data before booking
  - after_booking(student, result) → process result after booking
  - on_error(student, error) → handle booking errors

Usage:
  from plugin_manager import plugin_manager

  @plugin_manager.register("before_booking")
  def my_hook(student):
      student["notes"] = "processed by my plugin"
      return student

  # Enable/disable plugins at runtime
  plugin_manager.enable("my_hook")
  plugin_manager.disable("my_hook")

TODO:
  - Add plugin discovery (scan plugins/ directory)
  - Add plugin config via YAML/JSON
  - Add plugin isolation (sandboxing)
  - Add plugin dependencies
"""
from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

PLUGINS_DIR = Path(__file__).parent / "plugins"


class PluginError(Exception):
    pass


class PluginManager:
    def __init__(self):
        self._hooks: Dict[str, List[Dict]] = {}
        self._plugins: Dict[str, Any] = {}

    def register(self, hook_name: str, priority: int = 0):
        """Decorator to register a function as a hook handler."""

        def decorator(fn):
            if hook_name not in self._hooks:
                self._hooks[hook_name] = []
            self._hooks[hook_name].append({"fn": fn, "priority": priority, "enabled": True})
            self._hooks[hook_name].sort(key=lambda x: x["priority"], reverse=True)
            return fn

        return decorator

    def enable(self, fn_name: str):
        for hook_list in self._hooks.values():
            for h in hook_list:
                if h["fn"].__name__ == fn_name:
                    h["enabled"] = True

    def disable(self, fn_name: str):
        for hook_list in self._hooks.values():
            for h in hook_list:
                if h["fn"].__name__ == fn_name:
                    h["enabled"] = False

    def run_hooks(self, hook_name: str, context: dict) -> dict:
        """Run all enabled handlers for a hook, passing context dict through."""
        for h in self._hooks.get(hook_name, []):
            if h["enabled"]:
                try:
                    result = h["fn"](context)
                    if isinstance(result, dict):
                        context = result
                except Exception as e:
                    raise PluginError(f"Plugin '{h['fn'].__name__}' failed: {e}") from e
        return context

    def discover(self):
        """Auto-discover plugins in the plugins/ directory."""
        if not PLUGINS_DIR.exists():
            PLUGINS_DIR.mkdir(exist_ok=True)
            (PLUGINS_DIR / "__init__.py").write_text("")
            return
        for f in sorted(PLUGINS_DIR.glob("*.py")):
            if f.name == "__init__.py":
                continue
            mod_name = f"plugins.{f.stem}"
            try:
                mod = importlib.import_module(mod_name)
                self._plugins[mod_name] = mod
            except Exception:
                pass

    def list_hooks(self) -> Dict[str, List[str]]:
        return {
            hook: [h["fn"].__name__ for h in handlers if h["enabled"]]
            for hook, handlers in self._hooks.items()
        }


plugin_manager = PluginManager()
