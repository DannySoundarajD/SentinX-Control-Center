# -*- coding: utf-8 -*-
"""AI page – Sentinel AI status and configuration."""

from __future__ import annotations
from gi.repository import Gtk, GLib
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class AIPage(Gtk.Box):
    """Premium AI settings and status page."""

    def __init__(self) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=0,
            margin_start=24, margin_end=24, margin_top=24, margin_bottom=24
        )

        # ── Page header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_bottom(20)
        t = Gtk.Label(label="Sentinel AI")
        t.set_xalign(0)
        t.get_style_context().add_class("page-title")
        header.append(t)
        st = Gtk.Label(label="AI assistant status and configuration")
        st.set_xalign(0)
        st.get_style_context().add_class("page-subtitle")
        header.append(st)
        self.append(header)

        # ── Status card
        status_card = SettingsCard(title="Status", icon_name="security-high-symbolic")

        status_row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._status_badge = Gtk.Label(label="Idle")
        self._status_badge.get_style_context().add_class("badge")
        self._status_badge.get_style_context().add_class("green")
        status_row_box.append(self._status_badge)

        status_card.add(SettingsRow(
            "Sentinel AI Status",
            subtitle="Current operational state of the AI assistant",
            widget=self._status_badge
        ))
        status_card.add(SettingsRow("Model", subtitle="Sentinel v1 (local)"))
        status_card.add(SettingsRow("Mode", subtitle="Privacy-first – fully local, no data leaves your device"))
        self.append(status_card)

        # ── Configuration card
        config_card = SettingsCard(title="Configuration", icon_name="preferences-system-symbolic")

        ai_enabled_switch = Gtk.Switch()
        ai_enabled_switch.set_active(True)
        config_card.add(SettingsRow(
            "Enable AI Assistant",
            subtitle="Allow Sentinel to assist with system tasks",
            widget=ai_enabled_switch
        ))

        suggestions_switch = Gtk.Switch()
        suggestions_switch.set_active(True)
        config_card.add(SettingsRow(
            "Smart Suggestions",
            subtitle="Offer context-aware recommendations",
            widget=suggestions_switch
        ))

        privacy_switch = Gtk.Switch()
        privacy_switch.set_active(True)
        config_card.add(SettingsRow(
            "Privacy Mode",
            subtitle="All processing stays local – no telemetry or cloud calls",
            widget=privacy_switch
        ))

        self.append(config_card)

        # ── Coming soon card
        soon_card = SettingsCard(title="Coming Soon", icon_name="dialog-information-symbolic")
        features = [
            ("Natural Language App Launcher", "Open any app by typing its name or describing it"),
            ("System Health Advisor",         "AI-powered diagnostics and performance tips"),
            ("Adaptive Theme Engine",          "Automatically suggests themes based on time of day"),
            ("Voice Commands",                 "Hands-free control of your desktop"),
        ]
        for name, sub in features:
            row = SettingsRow(name, subtitle=sub)
            badge = Gtk.Label(label="Soon")
            badge.get_style_context().add_class("badge")
            badge.get_style_context().add_class("orange")
            row.append(badge)
            soon_card.add(row)

        self.append(soon_card)
