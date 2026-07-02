# -*- coding: utf-8 -*-
"""About page – provides version and attribution information.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from gi.repository import Gtk

from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class AboutPage(Gtk.Box):
    """Displays basic information about the Control Center application."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_start=12, margin_end=12, margin_top=12, margin_bottom=12)
        card = SettingsCard(title="About SentinX Control Center")
        self.append(card)

        # Application version – could be injected via a build step; fall back
        version = "0.1.0"
        # Attempt to read a VERSION file if it exists next to this module.
        version_file = Path(__file__).resolve().parents[1] / "VERSION"
        if version_file.is_file():
            try:
                version = version_file.read_text(encoding="utf-8").strip()
            except OSError:
                pass
        card.add(SettingsRow("Version", subtitle=version))
        card.add(SettingsRow("Python", subtitle=sys.version.split()[0]))
        gtk_version = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
        card.add(SettingsRow("GTK", subtitle=gtk_version))
        card.add(SettingsRow("Platform", subtitle=platform.system()))
        card.add(SettingsRow("License", subtitle="GPLv3"))
        card.add(SettingsRow("Source", subtitle="https://github.com/yourorg/sentinx-control-center"))
