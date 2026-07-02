# -*- coding: utf-8 -*-
"""Reusable card widget based on :class:`Adw.PreferencesGroup`.

The card groups related settings rows and optionally displays a title and
description, mimicking the look of GNOME Settings panels.
"""

from __future__ import annotations

from typing import Optional

from gi.repository import Gtk


class SettingsCard(Gtk.Box):
    def add(self, widget):
        """Compatibility wrapper – forwards to :meth:`Gtk.Box.append`."""
        self.append(widget)
    """A container for a logical group of settings.

    Parameters
    ----------
    title:
        Optional heading displayed above the group.
    description:
        Optional sub‑text rendered below the title.
    """

    def __init__(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        if title:
            title_label = Gtk.Label(label=title)
            title_label.set_xalign(0)
            self.append(title_label)
        if description:
            desc_label = Gtk.Label(label=description)
            desc_label.set_xalign(0)
            self.append(desc_label)
