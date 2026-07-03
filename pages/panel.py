# -*- coding: utf-8 -*-
"""Panel configuration page – premium design with live XFCE panel controls."""

from __future__ import annotations
from gi.repository import Gtk
from backend.panel import PanelConfig
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class PanelPage(Gtk.Box):
    """Premium page for XFCE panel configuration."""

    def __init__(self) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=0,
            margin_start=24, margin_end=24, margin_top=24, margin_bottom=24
        )
        self._panel = PanelConfig()

        # ── Page header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_bottom(20)
        t = Gtk.Label(label="Panel")
        t.set_xalign(0)
        t.get_style_context().add_class("page-title")
        header.append(t)
        st = Gtk.Label(label="Configure the SentinX desktop panel")
        st.set_xalign(0)
        st.get_style_context().add_class("page-subtitle")
        header.append(st)
        self.append(header)

        # ── Position & Layout card
        layout_card = SettingsCard(title="Position & Layout", icon_name="view-paged-symbolic")

        locked_switch = Gtk.Switch()
        self.locked_switch = locked_switch
        locked_switch.set_active(self._panel.get_position_locked())
        locked_switch.connect("state-set", self._on_position_locked_toggled)
        layout_card.add(SettingsRow(
            "Lock Panel Position",
            subtitle="Prevent the panel from being accidentally moved",
            widget=locked_switch
        ))

        size_adj = Gtk.Adjustment(value=self._panel.get_size(), lower=16, upper=128, step_increment=2)
        size_spin = Gtk.SpinButton(adjustment=size_adj, climb_rate=1.0, digits=0)
        self.size_spin = size_spin
        size_spin.connect("value-changed", self._on_size_changed)
        layout_card.add(SettingsRow(
            "Panel Size",
            subtitle="Height of the panel in pixels",
            widget=size_spin
        ))

        length_adj = Gtk.Adjustment(value=self._panel.get_length(), lower=10.0, upper=100.0, step_increment=1.0)
        length_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=length_adj)
        self.length_scale = length_scale
        length_scale.set_digits(0)
        length_scale.set_hexpand(True)
        length_scale.connect("value-changed", self._on_length_changed)
        layout_card.add(SettingsRow(
            "Panel Length",
            subtitle="Width of the panel as a percentage of the screen",
            widget=length_scale
        ))

        self.append(layout_card)

        # ── Behaviour card
        behav_card = SettingsCard(title="Behaviour", icon_name="system-run-symbolic")

        autohide_combo = Gtk.ComboBoxText()
        self.autohide_combo = autohide_combo
        autohide_combo.append("0", "Never")
        autohide_combo.append("1", "Intelligently")
        autohide_combo.append("2", "Always")
        autohide_combo.set_active_id(str(self._panel.get_autohide_behavior()))
        autohide_combo.connect("changed", self._on_autohide_changed)
        behav_card.add(SettingsRow(
            "Auto-Hide",
            subtitle="When to automatically hide the panel",
            widget=autohide_combo
        ))

        enter_op_adj = Gtk.Adjustment(value=self._panel.get_enter_opacity(), lower=0, upper=100, step_increment=5)
        enter_op_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=enter_op_adj)
        self.enter_op_scale = enter_op_scale
        enter_op_scale.set_digits(0)
        enter_op_scale.set_hexpand(True)
        enter_op_scale.connect("value-changed", self._on_enter_opacity_changed)
        behav_card.add(SettingsRow(
            "Hover Opacity",
            subtitle="Panel opacity when the mouse is over it (%)",
            widget=enter_op_scale
        ))

        leave_op_adj = Gtk.Adjustment(value=self._panel.get_leave_opacity(), lower=0, upper=100, step_increment=5)
        leave_op_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=leave_op_adj)
        self.leave_op_scale = leave_op_scale
        leave_op_scale.set_digits(0)
        leave_op_scale.set_hexpand(True)
        leave_op_scale.connect("value-changed", self._on_leave_opacity_changed)
        behav_card.add(SettingsRow(
            "Idle Opacity",
            subtitle="Panel opacity when the mouse is away (%)",
            widget=leave_op_scale
        ))

        self.append(behav_card)

        # ── Appearance card
        app_card = SettingsCard(title="Appearance", icon_name="preferences-desktop-theme-symbolic")

        dark_switch = Gtk.Switch()
        self.dark_switch = dark_switch
        dark_switch.set_active(self._panel.get_dark_mode())
        dark_switch.connect("state-set", self._on_dark_mode_toggled)
        app_card.add(SettingsRow(
            "Dark Theme",
            subtitle="Apply dark styling to the panel background",
            widget=dark_switch
        ))

        self.append(app_card)

        # ── Reset card
        reset_card = SettingsCard(title="Reset", icon_name="edit-undo-symbolic")
        reset_btn = Gtk.Button(label="Restore Default Settings")
        reset_btn.get_style_context().add_class("destructive-action")
        reset_btn.set_margin_start(20)
        reset_btn.set_margin_end(20)
        reset_btn.set_margin_top(8)
        reset_btn.set_margin_bottom(16)
        reset_btn.connect("clicked", self._on_reset_clicked)
        reset_card.add(reset_btn)
        self.append(reset_card)

    # ─────────────────────────────────────────────────────────
    def _on_position_locked_toggled(self, switch, state):
        self._panel.set_position_locked(state)
        return False

    def _on_size_changed(self, spin):
        self._panel.set_size(int(spin.get_value()))

    def _on_length_changed(self, scale):
        self._panel.set_length(scale.get_value())

    def _on_autohide_changed(self, combo):
        self._panel.set_autohide_behavior(int(combo.get_active_id() or "0"))

    def _on_enter_opacity_changed(self, scale):
        self._panel.set_enter_opacity(int(scale.get_value()))

    def _on_leave_opacity_changed(self, scale):
        self._panel.set_leave_opacity(int(scale.get_value()))

    def _on_dark_mode_toggled(self, switch, state):
        self._panel.set_dark_mode(state)
        return False

    def _on_reset_clicked(self, btn):
        self._panel.reset_to_defaults()
        self.locked_switch.set_active(self._panel.get_position_locked())
        self.size_spin.set_value(self._panel.get_size())
        self.length_scale.set_value(self._panel.get_length())
        self.autohide_combo.set_active_id(str(self._panel.get_autohide_behavior()))
        self.enter_op_scale.set_value(self._panel.get_enter_opacity())
        self.leave_op_scale.set_value(self._panel.get_leave_opacity())
        self.dark_switch.set_active(self._panel.get_dark_mode())
