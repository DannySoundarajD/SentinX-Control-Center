# -*- coding: utf-8 -*-
"""AI page – placeholder for future Sentinel and other model integrations.
"""

from __future__ import annotations

from gi.repository import Gtk


class AIPage(Gtk.Box):
    """Placeholder page for AI configuration and status display."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_start=12, margin_end=12, margin_top=12, margin_bottom=12)
        label = Gtk.Label(label="AI integration UI will be implemented in the future.")
        label.set_margin_top(24)
        self.append(label)
