# -*- coding: utf-8 -*-
"""Header bar used at the top of the main window.

The header simply displays the application title and, because it inherits from
:class:`Adw.HeaderBar`, automatically provides the standard window controls.
"""

from __future__ import annotations

from gi.repository import Gtk


class Header(Gtk.HeaderBar):
    """Standardised header bar for the Control Center window."""

    def __init__(self) -> None:
        super().__init__()
        self.set_title("SentinX Control Center")
        self.set_show_title(True)
        self.set_show_end_title_buttons(True)
