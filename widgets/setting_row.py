# -*- coding: utf-8 -*-
"""Premium SettingsRow widget with proper left/right layout."""

from __future__ import annotations
from gi.repository import Gtk


class SettingsRow(Gtk.Box):
    """A premium row: title + optional subtitle on the left, widget on the right."""

    def __init__(self, title: str, subtitle: str | None = None,
                 widget: Gtk.Widget | None = None) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.get_style_context().add_class("setting-row")

        # Left side: title + subtitle stacked vertically
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        left.set_hexpand(True)
        left.set_valign(Gtk.Align.CENTER)

        self._title_label = Gtk.Label(label=title)
        self._title_label.set_xalign(0)
        self._title_label.get_style_context().add_class("setting-title")
        left.append(self._title_label)

        self._subtitle_label = None
        if subtitle is not None:
            self._subtitle_label = Gtk.Label(label=subtitle)
            self._subtitle_label.set_xalign(0)
            self._subtitle_label.get_style_context().add_class("setting-subtitle")
            left.append(self._subtitle_label)

        self.append(left)

        # Right side: optional control widget
        if widget is not None:
            widget.set_valign(Gtk.Align.CENTER)
            self.append(widget)

    def set_subtitle(self, subtitle: str | None) -> None:
        """Dynamically update or hide the subtitle text."""
        if subtitle is None:
            if self._subtitle_label:
                self._subtitle_label.set_visible(False)
            return

        if self._subtitle_label is None:
            self._subtitle_label = Gtk.Label(label=subtitle)
            self._subtitle_label.set_xalign(0)
            self._subtitle_label.get_style_context().add_class("setting-subtitle")
            left = self.get_first_child()
            left.append(self._subtitle_label)

        self._subtitle_label.set_label(subtitle)
        self._subtitle_label.set_visible(True)

    def get_subtitle(self) -> str | None:
        if self._subtitle_label:
            return self._subtitle_label.get_label()
        return None
