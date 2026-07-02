# -*- coding: utf-8 -*-
"""Appearance page – allows the user to tweak visual aspects of the desktop.

Only a subset of the settings described in the specification are implemented
here.  Each widget writes its value back to the JSON backend immediately.
"""

from __future__ import annotations

from pathlib import Path
import subprocess

from gi.repository import Gtk, Gdk, Gio

from backend.config import Config
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class AppearancePage(Gtk.Box):
    """Page that edits appearance‑related configuration values."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_start=12, margin_end=12, margin_top=12, margin_bottom=12)

        # Load (or create) the appearance configuration file.
        default_cfg = {
            "dark_mode": False,
            "accent_color": "#3584e4",
            "wallpaper": "",
            "transparency": 0.0,
            "animations": True,
            "icon_theme": "default",
            "font": "Sans 11",
            "cursor_theme": "default",
            "corner_radius": 4,
        }
        self._cfg = Config("appearance", default_cfg)

        # Apply correct theme at application startup
        dark = bool(self._cfg.get("dark_mode", False))
        try:
            settings = Gtk.Settings.get_default()
            if settings:
                settings.set_property("gtk-application-prefer-dark-theme", dark)
        except Exception:
            pass

        card = SettingsCard(title="Appearance")
        self.append(card)

        # Dark mode ----------------------------------------------------------
        dark_switch = Gtk.Switch()
        dark_switch.set_active(bool(self._cfg.get("dark_mode", False)))
        dark_switch.connect("state-set", self._on_dark_mode_toggled)
        card.add(SettingsRow("Dark mode", widget=dark_switch))

        # Accent colour ------------------------------------------------------
        accent_entry = Gtk.Entry()
        accent_entry.set_text(str(self._cfg.get("accent_color", "#3584e4")))
        accent_entry.set_placeholder_text("#RRGGBB")
        accent_entry.connect("changed", self._on_accent_changed)
        card.add(SettingsRow("Accent colour", widget=accent_entry))

        # Wallpaper ----------------------------------------------------------
        wallpaper_button = Gtk.Button(label="Select wallpaper")
        wallpaper_button.connect("clicked", self._on_wallpaper_clicked)
        card.add(SettingsRow("Wallpaper", widget=wallpaper_button))

        # Transparency slider -------------------------------------------------
        transparency_adj = Gtk.Adjustment(value=float(self._cfg.get("transparency", 0.0)), lower=0.0, upper=1.0, step_increment=0.05)
        transparency_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=transparency_adj)
        transparency_scale.set_digits(2)
        transparency_scale.set_hexpand(True)
        transparency_scale.connect("value-changed", self._on_transparency_changed)
        card.add(SettingsRow("Transparency", widget=transparency_scale))

    # ---------------------------------------------------------------------
    # Signal callbacks – each writes back to the JSON config immediately.
    # ---------------------------------------------------------------------
    def _on_dark_mode_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        self._cfg.set("dark_mode", state)
        apply_xfce_dark_mode(state)
        return False  # allow further processing

    def _on_accent_changed(self, entry: Gtk.Entry) -> None:
        self._cfg.set("accent_color", entry.get_text())

    def _on_wallpaper_selected(self, chooser: Gtk.FileChooserButton) -> None:
        file = chooser.get_file()
        if file:
            self._cfg.set("wallpaper", file.get_path())

    def _on_transparency_changed(self, scale: Gtk.Scale) -> None:
        self._cfg.set("transparency", scale.get_value())

    def _on_wallpaper_clicked(self, button: Gtk.Button) -> None:
        """Open a file chooser to select a wallpaper and store its path."""
        dialog = Gtk.FileChooserNative(
            title="Select Wallpaper",
            transient_for=self.get_root(),
            modal=True,
            action=Gtk.FileChooserAction.OPEN,
        )
        # Filter to image files (optional)
        filter_img = Gtk.FileFilter()
        filter_img.set_name("Image files")
        filter_img.add_mime_type("image/*")
        dialog.add_filter(filter_img)
        def _on_response(d, response_id):
            if response_id == Gtk.ResponseType.ACCEPT:
                file_obj = d.get_file()
                if file_obj:
                    file_path = file_obj.get_path()
                    self._cfg.set("wallpaper", file_path)
                    apply_xfce_wallpaper(file_path)
            d.destroy()

        dialog.connect("response", _on_response)
        dialog.show()


def apply_xfce_wallpaper(image_path: str) -> None:
    """Apply the wallpaper to all connected monitors and workspaces in XFCE."""
    try:
        monitors = ["monitor0"]
        try:
            res = subprocess.run(["xrandr"], capture_output=True, text=True, check=True)
            for line in res.stdout.split("\n"):
                if " connected" in line:
                    mon_name = line.split()[0]
                    monitors.append(f"monitor{mon_name}")
        except Exception:
            pass

        monitors = list(set(monitors))

        for monitor in monitors:
            for workspace in ["workspace0", "workspace1", "workspace2", "workspace3"]:
                base_prop = f"/backdrop/screen0/{monitor}/{workspace}"
                
                # Update both last-image and image-path to ensure compatibility
                subprocess.run(
                    ["xfconf-query", "-c", "xfce4-desktop", "-p", f"{base_prop}/last-image", "-s", image_path, "--create", "-t", "string"],
                    capture_output=True,
                    check=False
                )
                subprocess.run(
                    ["xfconf-query", "-c", "xfce4-desktop", "-p", f"{base_prop}/image-path", "-s", image_path, "--create", "-t", "string"],
                    capture_output=True,
                    check=False
                )
                # Set image style to Zoom (5)
                subprocess.run(
                    ["xfconf-query", "-c", "xfce4-desktop", "-p", f"{base_prop}/image-style", "-s", "5", "--create", "-t", "int"],
                    capture_output=True,
                    check=False
                )

        # Force xfdesktop to reload and redraw the wallpaper instantly
        subprocess.run(["xfdesktop", "--reload"], capture_output=True, check=False)
    except Exception as e:
        print(f"[apply_xfce_wallpaper] Failed to set wallpaper: {e}")


def apply_xfce_dark_mode(dark: bool) -> None:
    """Toggle XFCE dark mode by switching between dark/light themes."""
    # 1. Update the control center application's own theme
    try:
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", dark)
    except Exception as e:
        print(f"[apply_xfce_dark_mode] Failed to set GTK settings: {e}")

    # 2. Update the system-wide GTK theme in xsettings
    try:
        res = subprocess.run(
            ["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"],
            capture_output=True,
            text=True,
            check=True
        )
        current_theme = res.stdout.strip()
    except Exception:
        current_theme = "Adwaita"

    # Toggle logic
    if dark:
        if not current_theme.endswith("-dark") and current_theme != "Adwaita-dark":
            next_theme = current_theme + "-dark"
            if not theme_exists(next_theme):
                next_theme = "Adwaita-dark"
        else:
            next_theme = current_theme
    else:
        if current_theme.endswith("-dark"):
            next_theme = current_theme[:-5]
        elif current_theme == "Adwaita-dark":
            next_theme = "Adwaita"
        else:
            next_theme = current_theme

    try:
        subprocess.run(
            ["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", next_theme],
            capture_output=True,
            check=True
        )
    except Exception as e:
        print(f"[apply_xfce_dark_mode] Failed to set system theme: {e}")

    # 3. Update XFCE panel settings to synchronize with the theme
    try:
        # Set panel dark mode setting
        subprocess.run(
            ["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/dark-mode", "-s", str(dark).lower(), "--create", "-t", "bool"],
            capture_output=True,
            check=False
        )
        # Force panel to follow system theme (0) so it updates colors immediately
        subprocess.run(
            ["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-1/background-style", "-s", "0", "--create", "-t", "int"],
            capture_output=True,
            check=False
        )
    except Exception as e:
        print(f"[apply_xfce_dark_mode] Failed to set panel theme settings: {e}")


def theme_exists(theme_name: str) -> bool:
    """Check if a theme exists on the system."""
    return (Path("/usr/share/themes") / theme_name).is_dir() or (Path.home() / ".themes" / theme_name).is_dir()
