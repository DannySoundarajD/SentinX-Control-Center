# -*- coding: utf-8 -*-
"""Simple vertical box used as a visual section; optional title.
"""

from __future__ import annotations

from gi.repository import Gtk


class SettingsSection(Gtk.Box):
    """Simple vertical box used as a visual section; optional title."""

    def __init__(self, title: str | None = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        if title:
            title_label = Gtk.Label(label=title)
            title_label.set_xalign(0)
            self.append(title_label)
