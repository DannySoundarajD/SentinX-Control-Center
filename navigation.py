# -*- coding: utf-8 -*-
"""Navigation manager – thin wrapper around a :class:`Gtk.Stack`.

The manager provides a ``show`` method that switches the visible child by name.
"""

from __future__ import annotations

from gi.repository import Gtk


class NavigationManager:
    """Helper that abstracts page switching for the main window."""

    def __init__(self, stack: Gtk.Stack) -> None:
        self._stack = stack

    def show(self, page_name: str) -> None:
        """Display the page identified by *page_name*.

        ``page_name`` must match the name used when the page widget was added
        to the underlying :class:`Gtk.Stack` via ``add_named``.
        """
        self._stack.set_visible_child_name(page_name)
