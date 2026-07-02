# -*- coding: utf-8 -*-
"""Simple search entry widget based on :class:`Adw.SearchEntry`.
"""

from __future__ import annotations

from gi.repository import Gtk


class SearchBar(Gtk.SearchEntry):
    """A thin wrapper that sets a default placeholder text."""

    def __init__(self, placeholder: str = "Search…") -> None:
        super().__init__()
        self.set_placeholder_text(placeholder)
