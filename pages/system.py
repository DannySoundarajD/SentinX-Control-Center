# -*- coding: utf-8 -*-
"""System page – premium design with power, hardware controls, and system info."""

from __future__ import annotations
import subprocess
import platform
from gi.repository import Gtk
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class EditHostnameDialog(Gtk.Dialog):
    """Dialog prompting the user to enter a new hostname."""

    def __init__(self, parent: Gtk.Window, current_hostname: str) -> None:
        super().__init__(title="Edit Hostname", transient_for=parent, modal=True)
        self.set_default_size(350, 150)

        content = self.get_content_area()
        content.set_spacing(12)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(12)

        lbl = Gtk.Label(label="Enter new hostname:")
        lbl.set_xalign(0)
        lbl.get_style_context().add_class("setting-title")
        content.append(lbl)

        self.entry = Gtk.Entry()
        self.entry.set_text(current_hostname)
        self.entry.set_hexpand(True)
        content.append(self.entry)

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        ok_btn = self.add_button("Apply", Gtk.ResponseType.ACCEPT)
        ok_btn.get_style_context().add_class("suggested-action")

    def get_hostname(self) -> str:
        return self.entry.get_text().strip()


class SystemPage(Gtk.Box):
    """Premium system settings page with editable hostname, volume, and brightness."""

    def __init__(self) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=0,
            margin_start=24, margin_end=24, margin_top=24, margin_bottom=24
        )

        # ── Page header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_bottom(20)
        t = Gtk.Label(label="System")
        t.set_xalign(0)
        t.get_style_context().add_class("page-title")
        header.append(t)
        st = Gtk.Label(label="System settings, power options, and hardware controls")
        st.set_xalign(0)
        st.get_style_context().add_class("page-subtitle")
        header.append(st)
        self.append(header)

        # ── System info card
        info_card = SettingsCard(title="System Information", icon_name="computer-symbolic")

        # Hostname edit container
        edit_hostname_btn = Gtk.Button(label="Edit")
        edit_hostname_btn.get_style_context().add_class("flat-action")
        edit_hostname_btn.connect("clicked", self._on_edit_hostname_clicked)

        hostname_row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hostname_row_box.set_valign(Gtk.Align.CENTER)
        self._hostname_label = Gtk.Label(label=platform.node())
        self._hostname_label.get_style_context().add_class("setting-subtitle")
        hostname_row_box.append(self._hostname_label)
        hostname_row_box.append(edit_hostname_btn)

        info_card.add(SettingsRow("Hostname", subtitle=None, widget=hostname_row_box))
        info_card.add(SettingsRow("OS", subtitle=self._get_os()))
        info_card.add(SettingsRow("Kernel", subtitle=platform.release()))
        info_card.add(SettingsRow("Architecture", subtitle=platform.machine()))
        self.append(info_card)

        # ── Hardware Controls Card
        hw_card = SettingsCard(title="Hardware Controls", icon_name="preferences-desktop-peripherals-symbolic")

        # Volume control
        self._vol_adj = Gtk.Adjustment(value=self._get_volume(), lower=0.0, upper=100.0, step_increment=5.0)
        vol_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self._vol_adj)
        vol_scale.set_digits(0)
        vol_scale.set_hexpand(True)
        vol_scale.connect("value-changed", self._on_volume_changed)

        # Mute button
        self._mute_btn = Gtk.Button()
        self._mute_btn.get_style_context().add_class("flat-action")
        self._update_mute_button_label()
        self._mute_btn.connect("clicked", self._on_mute_clicked)

        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        vol_box.append(vol_scale)
        vol_box.append(self._mute_btn)

        hw_card.add(SettingsRow("Audio Volume", subtitle="Adjust master system volume", widget=vol_box))

        # Brightness control
        self._bright_adj = Gtk.Adjustment(value=self._get_brightness(), lower=10.0, upper=100.0, step_increment=5.0)
        bright_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self._bright_adj)
        bright_scale.set_digits(0)
        bright_scale.set_hexpand(True)
        bright_scale.connect("value-changed", self._on_brightness_changed)

        hw_card.add(SettingsRow("Screen Brightness", subtitle="Adjust screen backlighting level", widget=bright_scale))

        self.append(hw_card)

        # ── Power card
        power_card = SettingsCard(title="Power", icon_name="system-shutdown-symbolic")

        suspend_btn = Gtk.Button(label="Suspend")
        suspend_btn.get_style_context().add_class("flat-action")
        suspend_btn.connect("clicked", lambda _: self._run("systemctl suspend"))
        power_card.add(SettingsRow("Suspend System", subtitle="Put the computer into low-power sleep mode", widget=suspend_btn))

        reboot_btn = Gtk.Button(label="Reboot")
        reboot_btn.get_style_context().add_class("flat-action")
        reboot_btn.connect("clicked", lambda _: self._run("systemctl reboot"))
        power_card.add(SettingsRow("Reboot", subtitle="Restart the computer", widget=reboot_btn))

        shutdown_btn = Gtk.Button(label="Shut Down")
        shutdown_btn.get_style_context().add_class("destructive-action")
        shutdown_btn.connect("clicked", lambda _: self._run("systemctl poweroff"))
        power_card.add(SettingsRow("Shut Down", subtitle="Power off the computer", widget=shutdown_btn))

        self.append(power_card)

        # ── Display settings shortcut card
        display_card = SettingsCard(title="Display", icon_name="video-display-symbolic")

        xfce_disp_btn = Gtk.Button(label="Open Display Settings")
        xfce_disp_btn.get_style_context().add_class("flat-action")
        xfce_disp_btn.connect("clicked", lambda _: self._launch("xfce4-display-settings"))
        display_card.add(SettingsRow("XFCE Display Settings", subtitle="Configure resolution, refresh rate, and multi-monitor layout", widget=xfce_disp_btn))

        self.append(display_card)

        # ── Default apps / shortcuts card
        apps_card = SettingsCard(title="Default Applications", icon_name="system-run-symbolic")

        mime_btn = Gtk.Button(label="Open Settings")
        mime_btn.get_style_context().add_class("flat-action")
        mime_btn.connect("clicked", lambda _: self._launch("xfce4-mime-settings"))
        apps_card.add(SettingsRow("Default Apps", subtitle="Configure default applications for file types", widget=mime_btn))

        self.append(apps_card)

    def _get_os(self) -> str:
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass
        return platform.system()

    def _get_volume(self) -> float:
        try:
            res = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True, check=True)
            for word in res.stdout.split():
                if "%" in word:
                    return float(word.replace("%", ""))
        except Exception:
            pass
        return 50.0

    def _get_brightness(self) -> float:
        try:
            res = subprocess.run(["xrandr", "--verbose"], capture_output=True, text=True, check=True)
            for line in res.stdout.split("\n"):
                if "Brightness:" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        return float(parts[1].strip()) * 100.0
        except Exception:
            pass
        return 100.0

    def _on_volume_changed(self, scale: Gtk.Scale) -> None:
        val = int(scale.get_value())
        try:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"], check=False)
        except Exception:
            pass

    def _on_brightness_changed(self, scale: Gtk.Scale) -> None:
        val = int(scale.get_value())
        float_val = max(10, min(100, val)) / 100.0
        try:
            res = subprocess.run(["xrandr"], capture_output=True, text=True, check=True)
            for line in res.stdout.split("\n"):
                if " connected" in line:
                    out = line.split()[0]
                    subprocess.run(["xrandr", "--output", out, "--brightness", f"{float_val:.2f}"], check=False)
        except Exception:
            pass

    def _on_mute_clicked(self, btn: Gtk.Button) -> None:
        try:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], check=False)
            self._update_mute_button_label()
        except Exception:
            pass

    def _update_mute_button_label(self) -> None:
        try:
            res = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True, check=True)
            muted = "yes" in res.stdout.lower()
        except Exception:
            muted = False

        if muted:
            self._mute_btn.set_label("🔇 Muted")
            self._mute_btn.get_style_context().add_class("destructive-action")
        else:
            self._mute_btn.set_label("🔊 Mute")
            self._mute_btn.get_style_context().remove_class("destructive-action")

    def _on_edit_hostname_clicked(self, btn: Gtk.Button) -> None:
        current = platform.node()
        dialog = EditHostnameDialog(self.get_root(), current)

        def _on_response(d: EditHostnameDialog, resp: int) -> None:
            if resp == Gtk.ResponseType.ACCEPT:
                new_name = d.get_hostname()
                if new_name and new_name != current:
                    try:
                        res = subprocess.run(
                            ["pkexec", "hostnamectl", "set-hostname", new_name],
                            capture_output=True, text=True
                        )
                        if res.returncode == 0:
                            self._hostname_label.set_label(new_name)
                        else:
                            self._show_error_dialog("Authentication failed or cancelled.")
                    except Exception as e:
                       self._show_error_dialog(f"Error executing hostname change: {e}")
            d.destroy()

        dialog.connect("response", _on_response)
        dialog.show()

    def _show_error_dialog(self, message: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self.get_root(),
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show()

    def _run(self, cmd: str) -> None:
        try:
            subprocess.Popen(cmd.split())
        except Exception as e:
            print(f"[SystemPage] run error: {e}")

    def _launch(self, cmd: str) -> None:
        try:
            subprocess.Popen([cmd])
        except Exception as e:
            print(f"[SystemPage] launch error: {e}")
