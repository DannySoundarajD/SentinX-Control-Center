# -*- coding: utf-8 -*-
"""Application class for SentinX Control Center.

The class is a thin subclass of :class:`Adw.Application` that creates the main
window on activation.
"""

from __future__ import annotations

import gi

gi.require_version('Gtk', '4.0')
# gi.require_version('Adw', '1')  # Adwaita not needed for this app

from gi.repository import Gtk, Gio

from window import MainWindow


class SentinXApp(Gtk.Application):
    """Gtk.Application subclass that launches the Control Center UI."""

    def __init__(self) -> None:
        super().__init__(application_id="com.sentinx.ControlCenter", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self) -> None:
        # ``active_window`` returns ``None`` the first time the app is started.
        if not self.props.active_window:
            win = MainWindow(self)
            win.present()
        else:
            self.props.active_window.present()




