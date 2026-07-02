# -*- coding: utf-8 -*-
"""Row widget used inside a :class:`~widgets.card.SettingsCard`.

It is based on :class:`Adw.ActionRow` which nicely aligns a title on the left
and an arbitrary widget (switch, slider, dropdown, etc.) on the right.
"""

from __future__ import annotations

from gi.repository import Gtk


class SettingsRow(Gtk.Box):
    """A row that holds a label and an optional trailing widget.

    Parameters
    ----------
    title:
        The primary text displayed on the left.
    subtitle:
        Optional secondary text displayed under the title.
    widget:
        A :class:`Gtk.Widget` that will be attached to the end of the row.
    """

    def __init__(self, title: str, subtitle: str | None = None, widget: Gtk.Widget | None = None) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._title_label = Gtk.Label(label=title)
        self._title_label.set_xalign(0)
        self.append(self._title_label)
        self._subtitle_label = None
        if subtitle:
            self._subtitle_label = Gtk.Label(label=subtitle)
            self._subtitle_label.set_xalign(0)
            self.append(self._subtitle_label)
        if widget:
            self.append(widget)
            widget.show()

    def set_subtitle(self, subtitle: str | None) -> None:
        """Update the subtitle text."""
        if subtitle is None:
            if self._subtitle_label:
                self._subtitle_label.set_visible(False)
        else:
            if self._subtitle_label is None:
                self._subtitle_label = Gtk.Label(label=subtitle)
                self._subtitle_label.set_xalign(0)
                # Insert after title label (position 1)
                self.insert_child_after(self._subtitle_label, self._title_label)
            self._subtitle_label.set_label(subtitle)
            self._subtitle_label.set_visible(True)

    def get_subtitle(self) -> str | None:
        """Get the current subtitle text."""
        if self._subtitle_label:
            return self._subtitle_label.get_label()
        return None
