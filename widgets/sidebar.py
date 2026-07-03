# -*- coding: utf-8 -*-
"""Premium sidebar navigation widget."""

from __future__ import annotations
from gi.repository import Gtk, GObject


# Sidebar page definitions: (icon, label, page_id)
NAV_ITEMS = [
    ("view-dashboard-symbolic",   "Dashboard",  "dashboard"),
    ("preferences-desktop-wallpaper-symbolic", "Appearance", "appearance"),
    ("go-bottom-symbolic",        "Dock",       "dock"),
    ("view-paged-symbolic",       "Panel",      "panel"),
    ("computer-symbolic",         "AI",         "ai"),
    ("system-run-symbolic",       "System",     "system"),
    ("help-about-symbolic",       "About",      "about"),
]


class Sidebar(Gtk.Box):
    """Vertical navigation panel for the control center."""

    __gsignals__ = {
        "page-selected": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("sentinx-sidebar")

        # ── Logo/Header area
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header.get_style_context().add_class("sentinx-sidebar-header")

        logo_icon = Gtk.Image.new_from_icon_name("security-high-symbolic")
        logo_icon.set_pixel_size(32)
        logo_icon.set_margin_bottom(6)
        logo_icon.get_style_context().add_class("card-icon")
        header.append(logo_icon)

        title_lbl = Gtk.Label(label="SentinX")
        title_lbl.get_style_context().add_class("sentinx-logo-text")
        title_lbl.set_xalign(0.5)
        header.append(title_lbl)

        sub_lbl = Gtk.Label(label="CONTROL CENTER")
        sub_lbl.get_style_context().add_class("sentinx-logo-sub")
        sub_lbl.set_xalign(0.5)
        header.append(sub_lbl)

        self.append(header)

        # ── Navigation buttons
        nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        nav_box.set_margin_top(8)
        nav_box.set_margin_start(6)
        nav_box.set_margin_end(6)
        self.append(nav_box)

        self._buttons: dict[str, Gtk.Button] = {}
        self._active_id: str | None = None

        for icon_name, label_text, page_id in NAV_ITEMS:
            btn = self._make_nav_button(icon_name, label_text, page_id)
            nav_box.append(btn)
            self._buttons[page_id] = btn

        # Select first item by default
        first_id = NAV_ITEMS[0][2]
        self._set_active(first_id)

    def _make_nav_button(self, icon_name: str, label_text: str, page_id: str) -> Gtk.Button:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(4)

        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(16)
        box.append(icon)

        lbl = Gtk.Label(label=label_text)
        lbl.set_xalign(0)
        lbl.set_hexpand(True)
        box.append(lbl)

        btn = Gtk.Button()
        btn.set_child(box)
        btn.get_style_context().add_class("nav-button")
        btn.set_halign(Gtk.Align.FILL)
        btn.connect("clicked", self._on_nav_clicked, page_id)
        return btn

    def _set_active(self, page_id: str) -> None:
        if self._active_id and self._active_id in self._buttons:
            self._buttons[self._active_id].get_style_context().remove_class("active")
        self._active_id = page_id
        if page_id in self._buttons:
            self._buttons[page_id].get_style_context().add_class("active")

    def _on_nav_clicked(self, btn: Gtk.Button, page_id: str) -> None:
        self._set_active(page_id)
        self.emit("page-selected", page_id)
