# -*- coding: utf-8 -*-
"""Main application window – premium SentinX Control Center."""

from __future__ import annotations
import pathlib
from gi.repository import Gtk, Gdk

from widgets.sidebar import Sidebar
from navigation import NavigationManager

from pages.dashboard import DashboardPage
from pages.appearance import AppearancePage
from pages.dock import DockPage
from pages.panel import PanelPage
from pages.ai import AIPage
from pages.system import SystemPage
from pages.about import AboutPage


def _load_css() -> None:
    """Load and apply the premium CSS stylesheet."""
    css_path = pathlib.Path(__file__).resolve().parent / "resources" / "css" / "style.css"
    if not css_path.is_file():
        return
    provider = Gtk.CssProvider()
    provider.load_from_path(str(css_path))
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


class MainWindow(Gtk.ApplicationWindow):
    """Top-level window that houses the entire Control Center UI."""

    def __init__(self, app: Gtk.Application) -> None:
        super().__init__(application=app)
        self.set_default_size(1200, 780)
        self.set_title("SentinX Control Center")

        # Load premium CSS
        _load_css()

        # Apply dark theme preference
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", True)

        # Root resizable split container (Gtk.Paned)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(paned)

        # ── Sidebar
        self.sidebar = Sidebar()
        self.sidebar.set_size_request(180, -1)  # Minimum width constraint
        paned.set_start_child(self.sidebar)
        paned.set_resize_start_child(False)
        paned.set_shrink_start_child(False)

        # ── Content stack inside a scrolled window
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.get_style_context().add_class("page-scroll")
        paned.set_end_child(scroll)
        paned.set_resize_end_child(True)
        paned.set_shrink_end_child(False)

        # Default divider position
        paned.set_position(220)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(180)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        scroll.set_child(self.stack)

        # ── Register pages
        self._add_page("dashboard",  DashboardPage())
        self._add_page("appearance", AppearancePage())
        self._add_page("dock",       DockPage())
        self._add_page("panel",      PanelPage())
        self._add_page("ai",         AIPage())
        self._add_page("system",     SystemPage())
        self._add_page("about",      AboutPage())

        # ── Navigation
        self.nav = NavigationManager(self.stack)
        self.sidebar.connect("page-selected", self._on_page_selected)
        self.nav.show("dashboard")

    def _add_page(self, name: str, widget: Gtk.Widget) -> None:
        self.stack.add_named(widget, name)
        widget.show()

    def _on_page_selected(self, sidebar: Sidebar, page_name: str) -> None:
        self.nav.show(page_name)
