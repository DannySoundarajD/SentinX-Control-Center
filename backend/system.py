# -*- coding: utf-8 -*-
"""Backend stub for system‑level configuration.

Only a very small amount of functionality is required for the current UI – the
module provides a thin wrapper around the generic :class:`~backend.config.Config`
object so that future extensions can add real system integration without
changing the public API.
"""

from __future__ import annotations

from .config import Config

DEFAULT_SYSTEM_CONFIG = {
    # Future keys such as power‑saving, updates, etc. can be added here.
}


class SystemConfig:
    """Accessor for ``system.json``.

    The class mirrors the design of other backend modules: it loads the JSON
    file on demand, exposes a ``get``/``set`` API and persists changes
    immediately.
    """

    def __init__(self) -> None:
        self._cfg = Config("system", DEFAULT_SYSTEM_CONFIG)

    def get(self, key: str, default: object | None = None) -> object | None:
        return self._cfg.get(key, default)

    def set(self, key: str, value: object) -> None:
        self._cfg.set(key, value)

    def data(self) -> dict:
        """Return a copy of the entire configuration dictionary."""
        return self._cfg.data()
