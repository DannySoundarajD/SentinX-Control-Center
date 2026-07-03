# -*- coding: utf-8 -*-
"""Card widget – premium glassmorphism container for settings groups."""

from __future__ import annotations
from typing import Optional
from gi.repository import Gtk


class SettingsCard(Gtk.Box):
    """A premium card container for a logical group of settings."""

    def __init__(self, title: Optional[str] = None, description: Optional[str] = None,
                 icon_name: Optional[str] = None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("settings-card")

        if title:
            title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            title_row.get_style_context().add_class("card-title-row")

            if icon_name:
                icon = Gtk.Image.new_from_icon_name(icon_name)
                icon.set_pixel_size(14)
                icon.get_style_context().add_class("card-icon")
                title_row.append(icon)

            label = Gtk.Label(label=title)
            label.set_xalign(0)
            label.get_style_context().add_class("card-title")
            title_row.append(label)

            self.append(title_row)

        if description:
            desc_row = Gtk.Box()
            desc_row.set_margin_start(20)
            desc_row.set_margin_end(20)
            desc_row.set_margin_top(6)
            desc_label = Gtk.Label(label=description)
            desc_label.set_xalign(0)
            desc_label.set_wrap(True)
            desc_label.get_style_context().add_class("setting-subtitle")
            desc_row.append(desc_label)
            self.append(desc_row)

        # Inner content box
        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.append(self._content)

    def add(self, widget: Gtk.Widget) -> None:
        """Add a widget (usually SettingsRow) to the card body."""
        self._content.append(widget)
