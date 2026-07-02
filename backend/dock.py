# -*- coding: utf-8 -*-
"""Backend for Dock configuration.

Provides a thin wrapper around the generic :class:`~backend.config.Config`
object that stores settings in ``~/.config/sentinx/dock.json``.
"""

from __future__ import annotations

from typing import List, Any

from .config import Config
from gi.repository import Gio
import os
import pathlib

# Default dock configuration – values are deliberately simple but can be
# extended without breaking existing installations.
DEFAULT_DOCK_CONFIG = {
    "position": "bottom",          # one of: bottom, left, right, top
    "icon_size": 48,               # pixel size of dock icons
    "zoom": 1.0,                   # zoom factor (1.0 = no zoom)
    "transparency": 0.0,           # 0.0 – fully opaque, 1.0 – fully transparent
    "autohide": False,             # hide dock when not in use
    "spacing": 6,                  # pixel spacing between icons
    "animation_speed": 1.0,        # multiplier for animation duration
    "pinned_apps": [],             # list of .desktop IDs
}


class DockConfig:
    """Convenient accessor for the dock configuration file."""

    def __init__(self) -> None:
        self._cfg = Config("dock", DEFAULT_DOCK_CONFIG)
        # Ensure the GSettings schema directory points to the dock's compiled schemas.
        schema_dir = pathlib.Path("/home/danny/Desktop/SentinX-OS/Sentinel-Dock/source/sentinx-dock/data")
        compiled_dir = schema_dir / "gschemas.compiled"
        os.environ.setdefault('GSETTINGS_SCHEMA_DIR', str(schema_dir))
        # Compile the schemas if they are not yet compiled.
        if not compiled_dir.is_dir():
            try:
                import subprocess
                subprocess.run(['glib-compile-schemas', str(schema_dir)], check=True)
            except Exception as compile_err:
                print(f"[DockConfig] Failed to compile GSettings schemas: {compile_err}")
        # Load GSettings for the Plank dock (the default dock name is "dock1").
        try:
            self._gs = Gio.Settings.new_with_path('net.launchpad.plank.dock.settings', '/net/launchpad/plank/docks/dock1/')
        except Exception as e:
            # If GSettings schema is not available, fallback silently.
            self._gs = None
            print(f"[DockConfig] GSettings not available: {e}")
        # Sync JSON autohide flag with current GSettings state if possible.
        if self._gs:
            try:
                hide_mode = self._gs.get_string('hide-mode')
                # Plank uses 'auto' for autohide, anything else means off.
                self._cfg.set('autohide', hide_mode == 'auto')
                # Also sync pinned apps from GSettings.
                try:
                    pinned = list(self._gs.get_strv('dock-items'))
                    self._cfg.set('pinned_apps', pinned)
                except Exception:
                    pass
                # Persist JSON.
                self._cfg.save()
            except Exception:
                pass

    # Generic getter / setter used by the UI layer
    def get(self, key: str, default: Any | None = None) -> Any:
        return self._cfg.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._cfg.set(key, value)

    # Specific helpers for common settings ---------------------------------
    def get_position(self) -> str:
        return self._cfg.get("position", "bottom")

    def set_position(self, value: str) -> None:
        self._cfg.set("position", value)
        if self._gs:
            # GSettings expects the same string values.
            self._gs.set_string('position', value)

    def get_icon_size(self) -> int:
        return int(self._cfg.get("icon_size", 48))

    def set_icon_size(self, size: int) -> None:
        # Clamp the size to the valid GSettings range (24–128)
        clamped = max(24, min(128, int(size)))
        self._cfg.set("icon_size", clamped)
        if self._gs:
            self._gs.set_int('icon-size', clamped)

    def get_zoom(self) -> float:
        return float(self._cfg.get("zoom", 1.0))

    def set_zoom(self, zoom: float) -> None:
        self._cfg.set("zoom", float(zoom))
        if self._gs:
            enabled = zoom != 1.0
            percent = int(round(zoom * 100))
            # Ensure within allowed range (100–200)
            percent = max(100, min(200, percent))
            self._gs.set_boolean('zoom-enabled', enabled)
            self._gs.set_int('zoom-percent', percent)

    def get_transparency(self) -> float:
        return float(self._cfg.get("transparency", 0.0))

    def set_transparency(self, val: float) -> None:
        self._cfg.set("transparency", float(val))

    def get_autohide(self) -> bool:
        return bool(self._cfg.get("autohide", False))

    def set_autohide(self, flag: bool) -> None:
        self._cfg.set("autohide", bool(flag))
        if self._gs:
            # Map autohide to hide-mode: use 'auto' when enabled, else 'intelligent'
            hide_mode = 'auto' if flag else 'intelligent'
            self._gs.set_string('hide-mode', hide_mode)

    def get_spacing(self) -> int:
        return int(self._cfg.get("spacing", 6))

    def set_spacing(self, spacing: int) -> None:
        self._cfg.set("spacing", int(spacing))

    def get_animation_speed(self) -> float:
        return float(self._cfg.get("animation_speed", 1.0))

    def set_animation_speed(self, speed: float) -> None:
        self._cfg.set("animation_speed", float(speed))

    def get_pinned_apps(self) -> List[str]:
        """Return the list of pinned applications (desktop IDs).

        Preference is taken from GSettings ``dock-items`` if available;
        otherwise falls back to the JSON config (for backward compatibility).
        """
        if self._gs:
            try:
                return list(self._gs.get_strv('dock-items'))
            except Exception:
                pass
        # Fallback to JSON
        return list(self._cfg.get("pinned_apps", []))

    def set_pinned_apps(self, apps: List[str]) -> None:
        """Set the pinned applications both in GSettings and JSON.

        ``apps`` should be a list of ``.desktop`` file basenames.
        """
        if self._gs:
            try:
                self._gs.set_strv('dock-items', apps)
            except Exception:
                pass
        self._cfg.set("pinned_apps", list(apps))
        self._cfg.save()

        # Update physical .dockitem launcher files to sync running dock instantly
        launchers_dir = get_launchers_dir()
        active_dockitems = set()

        for app in apps:
            app_name = app
            if app.endswith(".desktop"):
                app_name = app[:-8]
            
            dockitem_name = f"{app_name}.dockitem"
            active_dockitems.add(dockitem_name)

            dockitem_path = launchers_dir / dockitem_name
            if not dockitem_path.is_file():
                desktop_path = find_desktop_file(app)
                if desktop_path:
                    try:
                        content = f"[PlankDockItemPreferences]\nLauncher=file://{desktop_path}\n"
                        with open(dockitem_path, "w", encoding="utf-8") as f:
                            f.write(content)
                    except Exception as e:
                        print(f"[DockConfig] Failed to write dockitem {dockitem_path}: {e}")

        # Remove deleted launcher dockitems
        try:
            for item_path in launchers_dir.glob("*.dockitem"):
                if item_path.name not in active_dockitems:
                    item_path.unlink()
        except Exception as e:
            print(f"[DockConfig] Failed to clean up removed dockitems: {e}")

    # Convenience methods for pinned apps (UI helpers)
    def add_pinned_app(self, app: str) -> None:
        apps = self.get_pinned_apps()
        if app not in apps:
            apps.append(app)
            self.set_pinned_apps(apps)

    def remove_pinned_app(self, app: str) -> None:
        apps = self.get_pinned_apps()
        if app in apps:
            apps.remove(app)
            self.set_pinned_apps(apps)

    def reset_to_defaults(self) -> None:
        """Replace the current configuration with the factory defaults and sync GSettings."""
        # Reset JSON config to defaults.
        self._cfg.reset()
        # Apply defaults to GSettings to keep the dock in sync.
        # Each setter updates both JSON (already default) and GSettings.
        self.set_position(self.get_position())
        self.set_icon_size(self.get_icon_size())
        self.set_zoom(self.get_zoom())
        self.set_autohide(self.get_autohide())
        self.set_spacing(self.get_spacing())
        self.set_animation_speed(self.get_animation_speed())
        # Reset pinned apps in GSettings, launchers folder, and JSON
        self.set_pinned_apps([])


def get_launchers_dir() -> pathlib.Path:
    """Helper to locate Plank launchers directory."""
    paths = [
        pathlib.Path.home() / ".config" / "sentinx-dock" / "dock1" / "launchers",
        pathlib.Path.home() / ".config" / "plank" / "docks" / "dock1" / "launchers",
        pathlib.Path.home() / ".config" / "plank" / "dock1" / "launchers"
    ]
    for p in paths:
        if p.is_dir():
            return p
    # Fallback to sentinx-dock which is default for SentinX OS
    p = pathlib.Path.home() / ".config" / "sentinx-dock" / "dock1" / "launchers"
    p.mkdir(parents=True, exist_ok=True)
    return p


def find_desktop_file(app_id: str) -> pathlib.Path | None:
    """Helper to find the absolute path of a desktop file."""
    search_dirs = [
        pathlib.Path("/usr/share/applications"),
        pathlib.Path.home() / ".local" / "share" / "applications"
    ]
    for d in search_dirs:
        p = d / app_id
        if p.is_file():
            return p
    return None

