# -*- coding: utf-8 -*-
"""Backend for Panel configuration.

Provides a thin wrapper around the generic :class:`~backend.config.Config`
object that stores settings in ``~/.config/sentinx/panel.json`` and synchronizes
settings with XFCE panel configuration via ``xfconf-query``.
"""

from __future__ import annotations

import subprocess
from typing import Any, Dict
from .config import Config

DEFAULT_PANEL_CONFIG = {
    "size": 32,                     # panel height/size in pixels
    "length": 100.0,                # panel length in percent
    "autohide_behavior": 0,         # 0: Never, 1: Intelligently, 2: Always
    "position_locked": True,        # locked position flag
    "enter_opacity": 100,           # mouse-enter opacity (0-100)
    "leave_opacity": 100,           # mouse-leave opacity (0-100)
    "dark_mode": False,             # dark-mode panel theme flag
}


def _read_xfconf(prop: str, val_type: str) -> Any:
    """Helper to read property from xfce4-panel channel via xfconf-query."""
    try:
        res = subprocess.run(
            ["xfconf-query", "-c", "xfce4-panel", "-p", prop],
            capture_output=True,
            text=True,
            check=True
        )
        val = res.stdout.strip()
        if not val:
            return None
        if val_type == "bool":
            return val.lower() == "true"
        elif val_type == "int":
            return int(val)
        elif val_type == "double":
            return float(val)
        return val
    except Exception:
        return None


def _write_xfconf(prop: str, val: Any, val_type: str) -> None:
    """Helper to write property to xfce4-panel channel via xfconf-query."""
    try:
        val_str = str(val).lower() if val_type == "bool" else str(val)
        subprocess.run(
            ["xfconf-query", "-c", "xfce4-panel", "-p", prop, "-s", val_str, "--create", "-t", val_type],
            capture_output=True,
            check=True
        )
    except Exception as e:
        print(f"[PanelConfig] Failed to write xfconf property {prop} to {val}: {e}")


class PanelConfig:
    """Convenient accessor for the panel configuration file and active xfconf settings."""

    def __init__(self) -> None:
        self._cfg = Config("panel", DEFAULT_PANEL_CONFIG)
        self.sync_from_xfconf()

    def sync_from_xfconf(self) -> None:
        """Query active xfconf settings and update JSON configuration if successful."""
        size = _read_xfconf("/panels/panel-1/size", "int")
        if size is not None:
            self._cfg.set("size", size)

        length = _read_xfconf("/panels/panel-1/length", "double")
        if length is not None:
            self._cfg.set("length", length)

        autohide = _read_xfconf("/panels/panel-1/autohide-behavior", "int")
        if autohide is not None:
            self._cfg.set("autohide_behavior", autohide)

        locked = _read_xfconf("/panels/panel-1/position-locked", "bool")
        if locked is not None:
            self._cfg.set("position_locked", locked)

        enter_op = _read_xfconf("/panels/panel-1/enter-opacity", "int")
        if enter_op is not None:
            self._cfg.set("enter_opacity", enter_op)

        leave_op = _read_xfconf("/panels/panel-1/leave-opacity", "int")
        if leave_op is not None:
            self._cfg.set("leave_opacity", leave_op)

        dark = _read_xfconf("/panels/dark-mode", "bool")
        if dark is not None:
            self._cfg.set("dark_mode", dark)

        self._cfg.save()

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._cfg.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._cfg.set(key, value)

    def get_size(self) -> int:
        return int(self.get("size", 32))

    def set_size(self, size: int) -> None:
        self._cfg.set("size", int(size))
        _write_xfconf("/panels/panel-1/size", int(size), "int")

    def get_length(self) -> float:
        return float(self.get("length", 100.0))

    def set_length(self, length: float) -> None:
        self._cfg.set("length", float(length))
        _write_xfconf("/panels/panel-1/length", float(length), "double")

    def get_autohide_behavior(self) -> int:
        return int(self.get("autohide_behavior", 0))

    def set_autohide_behavior(self, behavior: int) -> None:
        self._cfg.set("autohide_behavior", int(behavior))
        _write_xfconf("/panels/panel-1/autohide-behavior", int(behavior), "int")

    def get_position_locked(self) -> bool:
        return bool(self.get("position_locked", True))

    def set_position_locked(self, locked: bool) -> None:
        self._cfg.set("position_locked", bool(locked))
        _write_xfconf("/panels/panel-1/position-locked", bool(locked), "bool")

    def get_enter_opacity(self) -> int:
        return int(self.get("enter_opacity", 100))

    def set_enter_opacity(self, opacity: int) -> None:
        self._cfg.set("enter_opacity", int(opacity))
        _write_xfconf("/panels/panel-1/enter-opacity", int(opacity), "int")

    def get_leave_opacity(self) -> int:
        return int(self.get("leave_opacity", 100))

    def set_leave_opacity(self, opacity: int) -> None:
        self._cfg.set("leave_opacity", int(opacity))
        _write_xfconf("/panels/panel-1/leave-opacity", int(opacity), "int")

    def get_dark_mode(self) -> bool:
        return bool(self.get("dark_mode", False))

    def set_dark_mode(self, dark: bool) -> None:
        self._cfg.set("dark_mode", bool(dark))
        _write_xfconf("/panels/dark-mode", bool(dark), "bool")

    def reset_to_defaults(self) -> None:
        """Reset JSON configuration and all active xfconf settings to factory defaults."""
        self._cfg.reset()
        self.set_size(self.get_size())
        self.set_length(self.get_length())
        self.set_autohide_behavior(self.get_autohide_behavior())
        self.set_position_locked(self.get_position_locked())
        self.set_enter_opacity(self.get_enter_opacity())
        self.set_leave_opacity(self.get_leave_opacity())
        self.set_dark_mode(self.get_dark_mode())
        self._cfg.save()
