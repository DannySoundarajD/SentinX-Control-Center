# -*- coding: utf-8 -*-
"""Dashboard page – provides a real-time overview of system status.

The page fetches actual system metrics using psutil and updates them periodically.
"""

from __future__ import annotations

import platform
import subprocess
from gi.repository import Gtk, GLib

import psutil

from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class DashboardPage(Gtk.Box):
    """Container for the dashboard overview cards with live data."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_start=12, margin_end=12, margin_top=12, margin_bottom=12)

        # Store row references for updates
        self._rows = {}

        # CPU card
        cpu_card = SettingsCard(title="CPU")
        self._rows["cpu_model"] = SettingsRow("Model", subtitle="")
        cpu_card.add(self._rows["cpu_model"])
        self._rows["cpu_usage"] = SettingsRow("Usage", subtitle="")
        cpu_card.add(self._rows["cpu_usage"])
        self.append(cpu_card)

        # RAM card
        ram_card = SettingsCard(title="Memory")
        self._rows["ram_total"] = SettingsRow("Total", subtitle="")
        ram_card.add(self._rows["ram_total"])
        self._rows["ram_used"] = SettingsRow("Used", subtitle="")
        ram_card.add(self._rows["ram_used"])
        self.append(ram_card)

        # GPU card
        gpu_card = SettingsCard(title="GPU")
        self._rows["gpu_model"] = SettingsRow("Model", subtitle="")
        gpu_card.add(self._rows["gpu_model"])
        self._rows["gpu_usage"] = SettingsRow("Usage", subtitle="")
        gpu_card.add(self._rows["gpu_usage"])
        self.append(gpu_card)

        # Storage card
        storage_card = SettingsCard(title="Storage")
        self._rows["storage_root"] = SettingsRow("Root", subtitle="")
        storage_card.add(self._rows["storage_root"])
        self._rows["storage_home"] = SettingsRow("Home", subtitle="")
        storage_card.add(self._rows["storage_home"])
        self.append(storage_card)

        # Battery card
        battery_card = SettingsCard(title="Battery")
        self._rows["battery_charge"] = SettingsRow("Charge", subtitle="")
        battery_card.add(self._rows["battery_charge"])
        self._rows["battery_state"] = SettingsRow("State", subtitle="")
        battery_card.add(self._rows["battery_state"])
        self.append(battery_card)

        # Dock status card
        dock_card = SettingsCard(title="Dock")
        self._rows["dock_pinned"] = SettingsRow("Pinned apps", subtitle="")
        dock_card.add(self._rows["dock_pinned"])
        self._rows["dock_position"] = SettingsRow("Position", subtitle="")
        dock_card.add(self._rows["dock_position"])
        self.append(dock_card)

        # Sentinel status card
        sentinel_card = SettingsCard(title="Sentinel AI")
        self._rows["sentinel_status"] = SettingsRow("Status", subtitle="")
        sentinel_card.add(self._rows["sentinel_status"])
        self.append(sentinel_card)

        # Updates card
        updates_card = SettingsCard(title="Updates")
        self._rows["updates_pending"] = SettingsRow("Pending", subtitle="")
        updates_card.add(self._rows["updates_pending"])
        self.append(updates_card)

        # Initial data fetch
        self._update_all()
        # Refresh every 5 seconds
        GLib.timeout_add_seconds(5, self._update_all)

    def _update_all(self) -> bool:
        """Update all metrics. Returns True to keep the timeout alive."""
        self._update_cpu()
        self._update_memory()
        self._update_gpu()
        self._update_storage()
        self._update_battery()
        self._update_dock()
        self._update_sentinel()
        self._update_updates()
        return True

    def _update_cpu(self) -> None:
        try:
            cpu_model = platform.processor() or "Unknown"
            self._rows["cpu_model"].set_subtitle(cpu_model)
            usage = psutil.cpu_percent(interval=None)
            self._rows["cpu_usage"].set_subtitle(f"{usage:.0f} %")
        except Exception:
            self._rows["cpu_model"].set_subtitle("Unknown")
            self._rows["cpu_usage"].set_subtitle("N/A")

    def _update_memory(self) -> None:
        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024**3)
            used_gb = mem.used / (1024**3)
            percent = mem.percent
            self._rows["ram_total"].set_subtitle(f"{total_gb:.1f} GB")
            self._rows["ram_used"].set_subtitle(f"{used_gb:.1f} GB ({percent:.0f} %)")
        except Exception:
            self._rows["ram_total"].set_subtitle("N/A")
            self._rows["ram_used"].set_subtitle("N/A")

    def _update_gpu(self) -> None:
        try:
            # Try nvidia-smi for NVIDIA GPUs
            result = subprocess.run(["nvidia-smi", "--query-gpu=name,utilization.gpu", "--format=csv,noheader,nounits"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                gpu_info = lines[0].split(', ')
                model = gpu_info[0]
                usage = gpu_info[1]
                self._rows["gpu_model"].set_subtitle(model)
                self._rows["gpu_usage"].set_subtitle(f"{usage} %")
            else:
                # Fallback: try to detect any GPU
                self._rows["gpu_model"].set_subtitle("Unknown")
                self._rows["gpu_usage"].set_subtitle("N/A")
        except Exception:
            self._rows["gpu_model"].set_subtitle("Unknown")
            self._rows["gpu_usage"].set_subtitle("N/A")

    def _update_storage(self) -> None:
        try:
            root = psutil.disk_usage('/')
            home = psutil.disk_usage('/home')
            self._rows["storage_root"].set_subtitle(f"{root.total/(1024**3):.0f} GB – {root.percent:.0f}% used")
            self._rows["storage_home"].set_subtitle(f"{home.total/(1024**3):.0f} GB – {home.percent:.0f}% used")
        except Exception:
            self._rows["storage_root"].set_subtitle("N/A")
            self._rows["storage_home"].set_subtitle("N/A")

    def _update_battery(self) -> None:
        try:
            battery = psutil.sensors_battery()
            if battery:
                self._rows["battery_charge"].set_subtitle(f"{battery.percent:.0f} %")
                state = "Charging" if battery.power_plugged else "Discharging"
                self._rows["battery_state"].set_subtitle(state)
            else:
                self._rows["battery_charge"].set_subtitle("No battery")
                self._rows["battery_state"].set_subtitle("N/A")
        except Exception:
            self._rows["battery_charge"].set_subtitle("N/A")
            self._rows["battery_state"].set_subtitle("N/A")

    def _update_dock(self) -> None:
        try:
            # Read from dock config
            from backend.dock import DockConfig
            dock = DockConfig()
            pinned = len(dock.get_pinned_apps())
            position = dock.get_position()
            self._rows["dock_pinned"].set_subtitle(str(pinned))
            self._rows["dock_position"].set_subtitle(position.capitalize())
        except Exception:
            self._rows["dock_pinned"].set_subtitle("N/A")
            self._rows["dock_position"].set_subtitle("N/A")

    def _update_sentinel(self) -> None:
        try:
            # Placeholder for Sentinel AI status
            self._rows["sentinel_status"].set_subtitle("Idle")
        except Exception:
            self._rows["sentinel_status"].set_subtitle("Unknown")

    def _update_updates(self) -> None:
        try:
            # Check for package updates (apt/dnf/pacman)
            for cmd in [["apt", "list", "--upgradable"], ["dnf", "check-update"], ["pacman", "-Qu"]]:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = [l for l in result.stdout.strip().split('\n') if l and not l.startswith('Listing')]
                        count = len(lines)
                        self._rows["updates_pending"].set_subtitle(f"{count} packages")
                        return
                except Exception:
                    continue
            self._rows["updates_pending"].set_subtitle("0 packages")
        except Exception:
            self._rows["updates_pending"].set_subtitle("N/A")
