# -*- coding: utf-8 -*-
"""Theme handling for SentinX Control Center.

The current implementation treats each ``*.css`` file inside the resources
``css`` directory as a theme. Loading a theme applies its stylesheet to the
default display using a :class:`Gtk.CssProvider`.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from gi.repository import Gtk, Gdk

# The directory that contains theme CSS files.  It lives two levels up from
# this module (``backend/`` → ``../resources/css``).
CSS_DIR = Path(__file__).resolve().parents[2] / "resources" / "css"


def list_themes() -> List[str]:
    """Return the names of all available themes.

    The name is derived from the filename without extension – for example a
    file ``dark.css`` becomes the theme name ``"dark"``.
    """
    if not CSS_DIR.is_dir():
        return []
    return [p.stem for p in CSS_DIR.glob("*.css") if p.is_file()]


def apply_theme(name: str) -> None:
    """Load *name*'s stylesheet and apply it to the entire application.

    Raises
    ------
    FileNotFoundError
        If the requested theme does not have a matching ``*.css`` file.
    """
    css_path = CSS_DIR / f"{name}.css"
    if not css_path.is_file():
        raise FileNotFoundError(f"Theme {name!r} not found in {CSS_DIR}")
    provider = Gtk.CssProvider()
    provider.load_from_path(str(css_path))
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("No GDK display available – GTK may not be initialised")
    Gtk.StyleContext.add_provider_for_display(
        display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
