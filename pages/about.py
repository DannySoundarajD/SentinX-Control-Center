# -*- coding: utf-8 -*-
"""About page – premium design with version and system info."""

from __future__ import annotations
import platform
import sys
from pathlib import Path
from gi.repository import Gtk
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class AboutPage(Gtk.Box):
    """Premium About page."""

    def __init__(self) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=0,
            margin_start=24, margin_end=24, margin_top=24, margin_bottom=24
        )

        # ── Page header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_bottom(24)
        t = Gtk.Label(label="About")
        t.set_xalign(0)
        t.get_style_context().add_class("page-title")
        header.append(t)
        st = Gtk.Label(label="SentinX Control Center – system information and credits")
        st.set_xalign(0)
        st.get_style_context().add_class("page-subtitle")
        header.append(st)
        self.append(header)

        # ── Logo hero card
        hero_card = SettingsCard()
        hero_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        hero_box.set_halign(Gtk.Align.CENTER)
        hero_box.set_margin_top(28)
        hero_box.set_margin_bottom(28)

        icon = Gtk.Image.new_from_icon_name("security-high-symbolic")
        icon.set_pixel_size(64)
        icon.get_style_context().add_class("card-icon")
        hero_box.append(icon)

        ver_lbl = Gtk.Label(label="SentinX Control Center")
        ver_lbl.get_style_context().add_class("about-version")
        hero_box.append(ver_lbl)

        tag_lbl = Gtk.Label(label="Your intelligent desktop companion for SentinX OS")
        tag_lbl.get_style_context().add_class("about-tagline")
        tag_lbl.set_justify(Gtk.Justification.CENTER)
        hero_box.append(tag_lbl)

        # Version badge
        version = "0.2.0"
        vf = Path(__file__).resolve().parents[1] / "VERSION"
        if vf.is_file():
            try:
                version = vf.read_text(encoding="utf-8").strip()
            except OSError:
                pass

        badge = Gtk.Label(label=f"v{version}")
        badge.get_style_context().add_class("badge")
        badge.set_halign(Gtk.Align.CENTER)
        hero_box.append(badge)

        hero_card.add(hero_box)
        self.append(hero_card)

        # ── Version info card
        info_card = SettingsCard(title="Build Information", icon_name="system-software-update-symbolic")
        info_card.add(SettingsRow("Version", subtitle=version))
        info_card.add(SettingsRow("Python", subtitle=sys.version.split()[0]))
        gtk_ver = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
        info_card.add(SettingsRow("GTK", subtitle=gtk_ver))
        info_card.add(SettingsRow("Platform", subtitle=f"{platform.system()} {platform.release()}"))
        info_card.add(SettingsRow("Architecture", subtitle=platform.machine()))
        self.append(info_card)

        # ── License card
        lic_card = SettingsCard(title="Legal", icon_name="help-about-symbolic")
        lic_card.add(SettingsRow("License", subtitle="GNU General Public License v3"))
        lic_card.add(SettingsRow(
            "Source Code",
            subtitle="github.com/DannySoundarajD/SentinX-Control-Center"
        ))
        lic_card.add(SettingsRow(
            "Copyright",
            subtitle="© 2025 Danny Soundaraj & SentinX OS Contributors"
        ))
        self.append(lic_card)
