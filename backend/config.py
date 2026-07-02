# -*- coding: utf-8 -*-
"""Backend configuration manager for SentinX Control Center.

Handles reading, writing, and default generation of JSON configuration files
stored under ``~/.config/sentinx/``. Each configuration file corresponds to a
feature area (appearance, dock, system, panel, sentinel).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# Base directory for all SentinX configuration files
CONFIG_DIR = Path.home() / ".config" / "sentinx"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    """Simple JSON‑backed configuration.

    Parameters
    ----------
    name:
        Base name of the configuration file (without ``.json``).
    default:
        A dictionary of default values used when the file does not exist.
    """

    def __init__(self, name: str, default: Dict[str, Any] | None = None) -> None:
        self.name = name
        self.path = CONFIG_DIR / f"{name}.json"
        self._default: Dict[str, Any] = default or {}
        self._data: Dict[str, Any] = {}
        self._load_or_create()

    # ---------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------
    def _load_or_create(self) -> None:
        """Load the JSON file if it exists, otherwise create it from defaults."""
        if self.path.is_file():
            self._load()
        else:
            self._data = self._default.copy()
            self.save()

    def _load(self) -> None:
        """Read the JSON file, falling back to defaults on error."""
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                self._data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            # Corrupted file – reset to defaults
            self._data = self._default.copy()
            self.save()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def get(self, key: str, default: Any | None = None) -> Any:
        """Return the value for *key* or *default* if missing."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set *key* to *value* and persist the file."""
        self._data[key] = value
        self.save()

    def save(self) -> None:
        """Write the current in‑memory representation to disk."""
        try:
            with self.path.open("w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise RuntimeError(f"Unable to write config {self.path!s}: {exc}") from exc

    def data(self) -> Dict[str, Any]:
        """Return a shallow copy of the whole configuration dictionary."""
        return self._data.copy()

    def reset(self) -> None:
        """Replace the file with the default values and persist them."""
        self._data = self._default.copy()
        self.save()
