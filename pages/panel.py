# -*- coding: utf-8 -*-
"""Panel configuration page – controls the XFCE panel properties.

The UI writes directly to ``panel.json`` and live-updates the active panel settings
via :class:`backend.panel.PanelConfig`.
"""

from __future__ import annotations

from gi.repository import Gtk

from backend.panel import PanelConfig
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class PanelPage(Gtk.Box):
    """Page that allows the user to edit panel preferences."""

    def __init__(self) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_start=12,
            margin_end=12,
            margin_top=12,
            margin_bottom=12
        )
        self._panel = PanelConfig()

        card = SettingsCard(title="Panel")
        self.append(card)

        # Position Locked ----------------------------------------------------
        locked_switch = Gtk.Switch()
        self.locked_switch = locked_switch
        locked_switch.set_active(self._panel.get_position_locked())
        locked_switch.connect("state-set", self._on_position_locked_toggled)
        card.add(SettingsRow("Lock panel position", widget=locked_switch))

        # Size ----------------------------------------------------------------
        size_adj = Gtk.Adjustment(value=self._panel.get_size(), lower=16, upper=128, step_increment=2)
        size_spin = Gtk.SpinButton(adjustment=size_adj, climb_rate=1.0, digits=0)
        self.size_spin = size_spin
        size_spin.connect("value-changed", self._on_size_changed)
        card.add(SettingsRow("Panel size (pixels)", widget=size_spin))

        # Length --------------------------------------------------------------
        length_adj = Gtk.Adjustment(value=self._panel.get_length(), lower=10.0, upper=100.0, step_increment=1.0)
        length_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=length_adj)
        self.length_scale = length_scale
        length_scale.set_digits(0)
        length_scale.set_hexpand(True)
        length_scale.connect("value-changed", self._on_length_changed)
        card.add(SettingsRow("Panel length (%)", widget=length_scale))

        # Autohide ------------------------------------------------------------
        autohide_combo = Gtk.ComboBoxText()
        self.autohide_combo = autohide_combo
        autohide_combo.append("0", "Never")
        autohide_combo.append("1", "Intelligently")
        autohide_combo.append("2", "Always")
        autohide_combo.set_active_id(str(self._panel.get_autohide_behavior()))
        autohide_combo.connect("changed", self._on_autohide_changed)
        card.add(SettingsRow("Auto‑hide behavior", widget=autohide_combo))

        # Enter Opacity -------------------------------------------------------
        enter_op_adj = Gtk.Adjustment(value=self._panel.get_enter_opacity(), lower=0, upper=100, step_increment=5)
        enter_op_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=enter_op_adj)
        self.enter_op_scale = enter_op_scale
        enter_op_scale.set_digits(0)
        enter_op_scale.set_hexpand(True)
        enter_op_scale.connect("value-changed", self._on_enter_opacity_changed)
        card.add(SettingsRow("Opacity on mouse hover (%)", widget=enter_op_scale))

        # Leave Opacity -------------------------------------------------------
        leave_op_adj = Gtk.Adjustment(value=self._panel.get_leave_opacity(), lower=0, upper=100, step_increment=5)
        leave_op_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=leave_op_adj)
        self.leave_op_scale = leave_op_scale
        leave_op_scale.set_digits(0)
        leave_op_scale.set_hexpand(True)
        leave_op_scale.connect("value-changed", self._on_leave_opacity_changed)
        card.add(SettingsRow("Opacity when mouse leaves (%)", widget=leave_op_scale))

        # Dark Mode ----------------------------------------------------------
        dark_switch = Gtk.Switch()
        self.dark_switch = dark_switch
        dark_switch.set_active(self._panel.get_dark_mode())
        dark_switch.connect("state-set", self._on_dark_mode_toggled)
        card.add(SettingsRow("Panel dark theme", widget=dark_switch))

        # Reset button -------------------------------------------------------
        reset_button = Gtk.Button(label="Restore defaults")
        reset_button.get_style_context().add_class("destructive-action")
        reset_button.connect("clicked", self._on_reset_clicked)
        card.add(reset_button)

    # ---------------------------------------------------------------------
    # Callbacks – each writes the new value to the backend.
    # ---------------------------------------------------------------------
    def _on_position_locked_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        self._panel.set_position_locked(state)
        return False

    def _on_size_changed(self, spin: Gtk.SpinButton) -> None:
        self._panel.set_size(int(spin.get_value()))

    def _on_length_changed(self, scale: Gtk.Scale) -> None:
        self._panel.set_length(scale.get_value())

    def _on_autohide_changed(self, combo: Gtk.ComboBoxText) -> None:
        active_id = combo.get_active_id() or "0"
        self._panel.set_autohide_behavior(int(active_id))

    def _on_enter_opacity_changed(self, scale: Gtk.Scale) -> None:
        self._panel.set_enter_opacity(int(scale.get_value()))

    def _on_leave_opacity_changed(self, scale: Gtk.Scale) -> None:
        self._panel.set_leave_opacity(int(scale.get_value()))

    def _on_dark_mode_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        self._panel.set_dark_mode(state)
        return False

    def _on_reset_clicked(self, btn: Gtk.Button) -> None:
        # Reset the underlying panel config to factory defaults
        self._panel.reset_to_defaults()
        # Bring UI widgets back in sync
        self.locked_switch.set_active(self._panel.get_position_locked())
        self.size_spin.set_value(self._panel.get_size())
        self.length_scale.set_value(self._panel.get_length())
        self.autohide_combo.set_active_id(str(self._panel.get_autohide_behavior()))
        self.enter_op_scale.set_value(self._panel.get_enter_opacity())
        self.leave_op_scale.set_value(self._panel.get_leave_opacity())
        self.dark_switch.set_active(self._panel.get_dark_mode())
