# -*- coding: utf-8 -*-
"""Placeholder backend for future Sentinel AI integration.

The class currently does nothing but offers a stable import location for the
UI code.  Future work will replace the methods with real RPC or library calls.
"""

from __future__ import annotations


class SentinelBackend:
    """Stub implementation – defined solely to keep the import path stable."""

    def __init__(self) -> None:
        pass

    def ping(self) -> bool:
        """Return ``True`` to indicate the stub is reachable.

        In a full implementation this would likely check the status of the
        AI service.
        """
        return True
