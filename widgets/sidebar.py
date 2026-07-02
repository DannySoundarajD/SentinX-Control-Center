# -*- coding: utf-8 -*-
"""Sidebar widget used for page navigation.

The widget is a simple :class:`Gtk.ListBox` where each row contains a button.
When a button is clicked the widget emits a custom ``"page-selected"`` signal
with the internal page identifier (e.g. ``"dashboard"``).
"""

from __future__ import annotations

from gi.repository import Gtk, GObject


class Sidebar(Gtk.ListBox):
    """Vertical navigation list used by the main window.

    The widget emits ``"page-selected"`` with a single *str* argument – the
    identifier of the page that should become visible.
    """

    __gsignals__ = {
        "page-selected": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self) -> None:
        super().__init__()
        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.set_activate_on_single_click(True)
        self._populate()
        self.show()

    def _populate(self) -> None:
        pages = [
            ("Dashboard", "dashboard"),
            ("Appearance", "appearance"),
            ("Dock", "dock"),
            ("Panel", "panel"),
            ("AI", "ai"),
            ("System", "system"),
            ("About", "about"),
        ]
        for label, name in pages:
            row = Gtk.ListBoxRow()
            button = Gtk.Button(label=label)
            button.set_halign(Gtk.Align.FILL)
            button.set_valign(Gtk.Align.CENTER)
            button.connect("clicked", lambda btn, n=name: self.emit("page-selected", n))
            row.set_child(button)
            self.append(row)
