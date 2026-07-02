# -*- coding: utf-8 -*-
"""Main application window.

The window follows the layout described in the specification:
* HeaderBar at the top (provided by the system)
* Fixed Sidebar on the left
* Content area on the right that swaps between pages via a :class:`Gtk.Stack`
"""

from __future__ import annotations

import pathlib

from gi.repository import Gtk

from widgets.sidebar import Sidebar
from navigation import NavigationManager

# Import page classes – each module defines a single public class with a matching name.
from pages.dashboard import DashboardPage
from pages.appearance import AppearancePage
from pages.dock import DockPage
from pages.panel import PanelPage
from pages.ai import AIPage
from pages.system import SystemPage
from pages.about import AboutPage


class MainWindow(Gtk.ApplicationWindow):
    """Top‑level window that houses the entire Control Center UI."""

    def __init__(self, app: Gtk.Application) -> None:
        super().__init__(application=app)
        self.set_default_size(1200, 760)
        self.set_title("SentinX Control Center")

        # Horizontal container
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_child(container)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.set_size_request(200, -1)  # reasonable width
        container.append(self.sidebar)

        # Content stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(200)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        container.append(self.stack)

        # Populate pages
        self._add_page("dashboard", DashboardPage())
        self._add_page("appearance", AppearancePage())
        self._add_page("dock", DockPage())
        self._add_page("panel", PanelPage())
        self._add_page("ai", AIPage())
        self._add_page("system", SystemPage())
        self._add_page("about", AboutPage())

        # Navigation handling
        self.nav = NavigationManager(self.stack)
        self.sidebar.connect("page-selected", self._on_page_selected)

        # Show the default page.
        self.nav.show("dashboard")

    # ---------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------
    def _add_page(self, name: str, widget: Gtk.Widget) -> None:
        """Add *widget* to the internal :class:`Gtk.Stack` under *name*."""
        self.stack.add_named(widget, name)
        widget.show()

    def _on_page_selected(self, sidebar: Sidebar, page_name: str) -> None:
        """Slot called when the sidebar emits ``page-selected``.
        The navigation manager then switches the stack.
        """
        self.nav.show(page_name)
