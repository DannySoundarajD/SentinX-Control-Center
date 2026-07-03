# -*- coding: utf-8 -*-
"""Appearance page – premium design with system-wide theme and wallpaper controls.

Features:
  • Dark mode toggle (system-wide via xfconf-query)
  • Accent colour picker with a Paint-style colour grid popup + hex codes
  • Wallpaper file chooser that immediately applies to all monitors
  • Transparency slider
"""

from __future__ import annotations

from pathlib import Path
import subprocess

from gi.repository import Gtk, Gdk, GLib

from backend.config import Config
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


# ── Curated colour palette (name, hex) ───────────────────────────────────────
COLOUR_PALETTE: list[tuple[str, str]] = [
    # Row 1 – blacks / whites
    ("Black",       "#000000"),
    ("Eerie Black", "#1a1a1a"),
    ("Dark Gray",   "#404040"),
    ("Gray",        "#808080"),
    ("Silver",      "#c0c0c0"),
    ("White",       "#ffffff"),
    # Row 2 – reds / pinks
    ("Dark Red",    "#8b0000"),
    ("Red",         "#ff0000"),
    ("Hot Pink",    "#ff69b4"),
    ("Rose",        "#ff007f"),
    ("Crimson",     "#dc143c"),
    ("Coral",       "#ff6b6b"),
    # Row 3 – oranges / yellows
    ("Brown",       "#8b4513"),
    ("Orange",      "#ff8c00"),
    ("Amber",       "#ffbf00"),
    ("Yellow",      "#ffff00"),
    ("Lime",        "#cddc39"),
    ("Chartreuse",  "#7fff00"),
    # Row 4 – greens
    ("Dark Green",  "#006400"),
    ("Green",       "#00b300"),
    ("Emerald",     "#50c878"),
    ("Mint",        "#98ff98"),
    ("Teal",        "#008080"),
    ("Cyan",        "#00e5ff"),
    # Row 5 – blues
    ("Navy",        "#003087"),
    ("Royal Blue",  "#4169e1"),
    ("Blue",        "#0057e7"),
    ("Sky Blue",    "#58a6ff"),
    ("Cornflower",  "#6495ed"),
    ("Steel Blue",  "#4682b4"),
    # Row 6 – purples / magentas
    ("Indigo",      "#4b0082"),
    ("Purple",      "#800080"),
    ("Violet",      "#ee82ee"),
    ("Magenta",     "#ff00ff"),
    ("Orchid",      "#da70d6"),
    ("Lavender",    "#9575cd"),
]

COLS = 6  # columns in the colour grid


class ColourPickerDialog(Gtk.Dialog):
    """Paint-style colour picker popup with a curated grid + hex code labels."""

    def __init__(self, parent: Gtk.Window, current_hex: str = "#3584e4") -> None:
        super().__init__(title="Choose Accent Colour", transient_for=parent, modal=True)
        self.set_default_size(420, 500)
        self._selected_hex = current_hex
        self._swatch_buttons: dict[str, Gtk.Button] = {}

        content = self.get_content_area()
        content.set_spacing(0)

        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        wrapper.set_margin_start(20)
        wrapper.set_margin_end(20)
        wrapper.set_margin_top(20)
        wrapper.set_margin_bottom(16)
        content.append(wrapper)

        # ── Title
        title_lbl = Gtk.Label(label="Select Accent Colour")
        title_lbl.get_style_context().add_class("page-title")
        title_lbl.set_xalign(0)
        title_lbl.set_margin_bottom(4)
        wrapper.append(title_lbl)

        sub_lbl = Gtk.Label(label="Pick from the palette or enter a hex code below")
        sub_lbl.get_style_context().add_class("page-subtitle")
        sub_lbl.set_xalign(0)
        wrapper.append(sub_lbl)

        # ── Scrolled colour grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        wrapper.append(scroll)

        grid_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scroll.set_child(grid_outer)

        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid_outer.append(grid)

        for idx, (name, hex_code) in enumerate(COLOUR_PALETTE):
            col = idx % COLS
            row = idx // COLS

            cell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            cell.set_halign(Gtk.Align.CENTER)

            btn = Gtk.Button()
            btn.set_size_request(44, 44)
            btn.get_style_context().add_class("color-swatch")
            btn.set_tooltip_text(f"{name}\n{hex_code}")
            self._apply_swatch_colour(btn, hex_code)

            if hex_code.lower() == current_hex.lower():
                btn.get_style_context().add_class("selected")

            btn.connect("clicked", self._on_swatch_clicked, hex_code)
            self._swatch_buttons[hex_code] = btn
            cell.append(btn)

            hex_lbl = Gtk.Label(label=hex_code.upper())
            hex_lbl.get_style_context().add_class("color-hex-label")
            cell.append(hex_lbl)

            grid.attach(cell, col, row, 1, 1)

        # ── Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        wrapper.append(sep)

        # ── Custom hex input row
        hex_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hex_row.set_margin_top(4)

        self._preview_box = Gtk.Box()
        self._preview_box.set_size_request(36, 36)
        self._preview_box.get_style_context().add_class("color-swatch")
        self._apply_swatch_colour_to_box(self._preview_box, current_hex)
        hex_row.append(self._preview_box)

        entry_lbl = Gtk.Label(label="Hex:")
        entry_lbl.get_style_context().add_class("setting-title")
        hex_row.append(entry_lbl)

        self._hex_entry = Gtk.Entry()
        self._hex_entry.set_text(current_hex.upper())
        self._hex_entry.set_hexpand(True)
        self._hex_entry.set_placeholder_text("#RRGGBB")
        self._hex_entry.set_max_length(7)
        self._hex_entry.connect("changed", self._on_hex_entry_changed)
        hex_row.append(self._hex_entry)

        wrapper.append(hex_row)

        # ── Dialog action buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        ok_btn = self.add_button("Apply Colour", Gtk.ResponseType.ACCEPT)
        ok_btn.get_style_context().add_class("suggested-action")

    def _apply_swatch_colour(self, btn: Gtk.Button, hex_code: str) -> None:
        """Apply background colour inline via CSS provider on the button."""
        try:
            r = int(hex_code[1:3], 16)
            g = int(hex_code[3:5], 16)
            b = int(hex_code[5:7], 16)
            css = f"button {{ background: rgb({r},{g},{b}); }}"
            provider = Gtk.CssProvider()
            provider.load_from_data(css.encode())
            btn.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception:
            pass

    def _apply_swatch_colour_to_box(self, box: Gtk.Box, hex_code: str) -> None:
        try:
            r = int(hex_code[1:3], 16)
            g = int(hex_code[3:5], 16)
            b = int(hex_code[5:7], 16)
            css = f"box {{ background: rgb({r},{g},{b}); }}"
            provider = Gtk.CssProvider()
            provider.load_from_data(css.encode())
            box.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception:
            pass

    def _on_swatch_clicked(self, btn: Gtk.Button, hex_code: str) -> None:
        # Deselect previous
        for hx, b in self._swatch_buttons.items():
            b.get_style_context().remove_class("selected")
        btn.get_style_context().add_class("selected")
        self._selected_hex = hex_code
        self._hex_entry.set_text(hex_code.upper())
        self._apply_swatch_colour_to_box(self._preview_box, hex_code)

    def _on_hex_entry_changed(self, entry: Gtk.Entry) -> None:
        text = entry.get_text().strip()
        if not text.startswith("#"):
            text = "#" + text
        if len(text) == 7:
            try:
                int(text[1:], 16)
                self._selected_hex = text
                self._apply_swatch_colour_to_box(self._preview_box, text)
                # Deselect palette swatches
                for b in self._swatch_buttons.values():
                    b.get_style_context().remove_class("selected")
                if text.lower() in self._swatch_buttons:
                    self._swatch_buttons[text.lower()].get_style_context().add_class("selected")
            except ValueError:
                pass

    def get_selected_colour(self) -> str:
        return self._selected_hex


# ── Appearance Page ───────────────────────────────────────────────────────────

class AppearancePage(Gtk.Box):
    """Premium appearance settings page."""

    def __init__(self) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=0,
            margin_start=24, margin_end=24, margin_top=24, margin_bottom=24
        )

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

        # Apply GTK dark theme and accent color at startup
        dark = bool(self._cfg.get("dark_mode", False))
        accent_color = str(self._cfg.get("accent_color", "#3584e4"))
        transparency = float(self._cfg.get("transparency", 0.0))
        
        try:
            s = Gtk.Settings.get_default()
            if s:
                s.set_property("gtk-application-prefer-dark-theme", dark)
        except Exception:
            pass

        apply_accent_color(accent_color)
        apply_xfwm4_transparency(transparency)

        # ── Page header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_bottom(20)

        t = Gtk.Label(label="Appearance")
        t.set_xalign(0)
        t.get_style_context().add_class("page-title")
        header.append(t)

        st = Gtk.Label(label="Customize the look and feel of your desktop")
        st.set_xalign(0)
        st.get_style_context().add_class("page-subtitle")
        header.append(st)
        self.append(header)

        # ── Theme card
        theme_card = SettingsCard(title="Theme", icon_name="preferences-desktop-theme-symbolic")

        dark_switch = Gtk.Switch()
        dark_switch.set_active(dark)
        dark_switch.connect("state-set", self._on_dark_mode_toggled)
        theme_card.add(SettingsRow(
            "Dark Mode",
            subtitle="Applies a dark theme system-wide (panel, apps, Whisker Menu)",
            widget=dark_switch
        ))

        # Accent colour – button that opens picker
        self._accent_hex = accent_color
        self._accent_btn = Gtk.Button()
        self._accent_btn.set_size_request(90, 34)
        self._update_accent_button()
        self._accent_btn.connect("clicked", self._on_accent_clicked)
        theme_card.add(SettingsRow(
            "Accent Colour",
            subtitle="Pick a highlight colour for the interface",
            widget=self._accent_btn
        ))

        self.append(theme_card)

        # ── Wallpaper card
        wall_card = SettingsCard(title="Wallpaper", icon_name="preferences-desktop-wallpaper-symbolic")

        # Current wallpaper preview label
        current_wall = str(self._cfg.get("wallpaper", ""))
        wall_name = Path(current_wall).name if current_wall else "None selected"
        self._wall_label = Gtk.Label(label=wall_name)
        self._wall_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self._wall_label.set_max_width_chars(28)
        self._wall_label.get_style_context().add_class("setting-subtitle")

        wall_btn = Gtk.Button(label="Browse…")
        wall_btn.get_style_context().add_class("flat-action")
        wall_btn.connect("clicked", self._on_wallpaper_clicked)

        wall_row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        wall_row_box.set_valign(Gtk.Align.CENTER)
        wall_row_box.append(self._wall_label)
        wall_row_box.append(wall_btn)

        wall_card.add(SettingsRow(
            "Desktop Wallpaper",
            subtitle="Applies instantly to all connected monitors",
            widget=wall_row_box
        ))

        self.append(wall_card)

        # ── Display card
        disp_card = SettingsCard(title="Display", icon_name="video-display-symbolic")

        trans_adj = Gtk.Adjustment(
            value=transparency,
            lower=0.0, upper=1.0, step_increment=0.05
        )
        trans_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=trans_adj)
        trans_scale.set_digits(2)
        trans_scale.set_hexpand(True)
        trans_scale.connect("value-changed", self._on_transparency_changed)
        disp_card.add(SettingsRow(
            "Transparency",
            subtitle="Dock / panel background transparency level",
            widget=trans_scale
        ))

        self.append(disp_card)

    # ─────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────
    def _update_accent_button(self) -> None:
        """Render the accent button with the current colour and hex text."""
        hx = self._accent_hex
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        swatch = Gtk.Box()
        swatch.set_size_request(18, 18)
        swatch.get_style_context().add_class("color-swatch")
        try:
            r = int(hx[1:3], 16)
            g = int(hx[3:5], 16)
            b = int(hx[5:7], 16)
            css = f"box {{ background: rgb({r},{g},{b}); border-radius: 4px; }}"
            provider = Gtk.CssProvider()
            provider.load_from_data(css.encode())
            swatch.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception:
            pass
        box.append(swatch)

        lbl = Gtk.Label(label=hx.upper())
        lbl.get_style_context().add_class("color-hex-label")
        box.append(lbl)

        self._accent_btn.set_child(box)

    # ─────────────────────────────────────────────────────────
    # Callbacks
    # ─────────────────────────────────────────────────────────
    def _on_dark_mode_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        self._cfg.set("dark_mode", state)
        apply_xfce_dark_mode(state)
        return False

    def _on_accent_clicked(self, btn: Gtk.Button) -> None:
        dialog = ColourPickerDialog(self.get_root(), self._accent_hex)

        def _on_response(d: ColourPickerDialog, resp: int) -> None:
            if resp == Gtk.ResponseType.ACCEPT:
                chosen = d.get_selected_colour()
                self._accent_hex = chosen
                self._cfg.set("accent_color", chosen)
                self._update_accent_button()
                apply_accent_color(chosen)
            d.destroy()

        dialog.connect("response", _on_response)
        dialog.show()

    def _on_wallpaper_clicked(self, btn: Gtk.Button) -> None:
        dialog = Gtk.FileChooserNative(
            title="Select Wallpaper",
            transient_for=self.get_root(),
            modal=True,
            action=Gtk.FileChooserAction.OPEN,
        )
        f = Gtk.FileFilter()
        f.set_name("Image files")
        f.add_mime_type("image/*")
        dialog.add_filter(f)

        def _on_response(d, resp):
            if resp == Gtk.ResponseType.ACCEPT:
                file_obj = d.get_file()
                if file_obj:
                    path = file_obj.get_path()
                    self._cfg.set("wallpaper", path)
                    self._wall_label.set_label(Path(path).name)
                    apply_xfce_wallpaper(path)
            d.destroy()

        dialog.connect("response", _on_response)
        dialog.show()

    def _on_transparency_changed(self, scale: Gtk.Scale) -> None:
        val = scale.get_value()
        self._cfg.set("transparency", val)
        apply_xfwm4_transparency(val)

    def _on_accent_changed(self, entry: Gtk.Entry) -> None:
        self._cfg.set("accent_color", entry.get_text())

    def _on_wallpaper_selected(self, chooser) -> None:
        file = chooser.get_file()
        if file:
            self._cfg.set("wallpaper", file.get_path())


# ── XFCE system helpers ───────────────────────────────────────────────────────

def apply_accent_color(hex_color: str) -> None:
    """Apply the accent color dynamically to the Control Center app via custom CSS injection."""
    try:
        css = f"""
        @define-color accent_color {hex_color};
        @define-color theme_selected_bg_color {hex_color};
        @define-color selected_bg_color {hex_color};
        
        switch:checked {{
            background: linear-gradient(135deg, {hex_color}, {hex_color});
            border-color: {hex_color};
        }}
        scale trough highlight {{
            background: {hex_color};
        }}
        scale slider {{
            border-color: {hex_color};
        }}
        button.suggested-action, button.action-button {{
            background: {hex_color};
            box-shadow: 0 4px 14px {hex_color}66;
        }}
        .nav-button.active, .nav-button:checked {{
            color: {hex_color};
            background: {hex_color}1a;
        }}
        .stat-value, .stat-icon, .card-icon {{
            color: {hex_color};
        }}
        progressbar progress {{
            background: {hex_color};
        }}
        .color-swatch.selected {{
            border-color: {hex_color};
            box-shadow: 0 0 0 3px {hex_color}4d;
        }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10
        )
    except Exception as e:
        print(f"[apply_accent_color] Failed to apply: {e}")


def apply_xfwm4_transparency(transparency: float) -> None:
    """Apply the transparency level (0.0 to 1.0) system-wide to XFWM4 windows and decorations."""
    # Convert slider value (0.0 opaque - 1.0 transparent) to opacity percentage (100 opaque - 0 transparent)
    opacity = int((1.0 - transparency) * 100)
    opacity = max(10, min(100, opacity)) # Don't let windows become completely invisible
    
    try:
        subprocess.run(
            ["xfconf-query", "-c", "xfwm4", "-p", "/general/inactive_opacity", "-s", str(opacity)],
            capture_output=True, check=False
        )
        subprocess.run(
            ["xfconf-query", "-c", "xfwm4", "-p", "/general/frame_opacity", "-s", str(opacity)],
            capture_output=True, check=False
        )
        subprocess.run(
            ["xfconf-query", "-c", "xfwm4", "-p", "/general/popup_opacity", "-s", str(opacity)],
            capture_output=True, check=False
        )
    except Exception as e:
        print(f"[apply_xfwm4_transparency] {e}")


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
                base = f"/backdrop/screen0/{monitor}/{workspace}"
                subprocess.run(
                    ["xfconf-query", "-c", "xfce4-desktop", "-p", f"{base}/last-image",
                     "-s", image_path, "--create", "-t", "string"],
                    capture_output=True, check=False
                )
                subprocess.run(
                    ["xfconf-query", "-c", "xfce4-desktop", "-p", f"{base}/image-path",
                     "-s", image_path, "--create", "-t", "string"],
                    capture_output=True, check=False
                )
                subprocess.run(
                    ["xfconf-query", "-c", "xfce4-desktop", "-p", f"{base}/image-style",
                     "-s", "5", "--create", "-t", "int"],
                    capture_output=True, check=False
                )

        subprocess.run(["xfdesktop", "--reload"], capture_output=True, check=False)
    except Exception as e:
        print(f"[apply_xfce_wallpaper] {e}")


def apply_xfce_dark_mode(dark: bool) -> None:
    """Toggle dark/light mode system-wide: GTK theme, panel, whisker menu."""
    # 1. Control Center itself
    try:
        s = Gtk.Settings.get_default()
        if s:
            s.set_property("gtk-application-prefer-dark-theme", dark)
    except Exception as e:
        print(f"[apply_xfce_dark_mode] GTK settings: {e}")

    # 2. System-wide GTK theme via xsettings
    try:
        res = subprocess.run(
            ["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"],
            capture_output=True, text=True, check=True
        )
        current = res.stdout.strip()
    except Exception:
        current = "Adwaita"

    if dark:
        if not current.endswith("-dark"):
            next_t = current + "-dark"
            if not theme_exists(next_t):
                next_t = "Adwaita-dark"
        else:
            next_t = current
    else:
        if current.endswith("-dark"):
            next_t = current[:-5]
        elif current == "Adwaita-dark":
            next_t = "Adwaita"
        else:
            next_t = current

    try:
        subprocess.run(
            ["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", next_t],
            capture_output=True, check=True
        )
    except Exception as e:
        print(f"[apply_xfce_dark_mode] xsettings: {e}")

    # 3. Panel & Whisker Menu
    try:
        subprocess.run(
            ["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/dark-mode",
             "-s", str(dark).lower(), "--create", "-t", "bool"],
            capture_output=True, check=False
        )
        subprocess.run(
            ["xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-1/background-style",
             "-s", "0", "--create", "-t", "int"],
            capture_output=True, check=False
        )
    except Exception as e:
        print(f"[apply_xfce_dark_mode] panel: {e}")


def theme_exists(name: str) -> bool:
    return (Path("/usr/share/themes") / name).is_dir() or (Path.home() / ".themes" / name).is_dir()
