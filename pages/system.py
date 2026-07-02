# -*- coding: utf-8 -*-
"""System page – placeholder for power, bluetooth, display, etc.
"""

from __future__ import annotations

from gi.repository import Gtk


class SystemPage(Gtk.Box):
    """Placeholder page for system‑level settings."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_start=12, margin_end=12, margin_top=12, margin_bottom=12)
        label = Gtk.Label(label="System settings UI will be added later.")
        label.set_margin_top(24)
        self.append(label)
