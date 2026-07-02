# -*- coding: utf-8 -*-
"""Dock configuration page – mirrors the settings exposed by the Vala dock.

The UI writes directly to ``dock.json`` via :class:`backend.dock.DockConfig`.
"""

from __future__ import annotations

from gi.repository import Gtk, Gdk, GObject, Gio
import pathlib

from backend.dock import DockConfig
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class DockPage(Gtk.Box):
    """Page that allows the user to edit dock preferences."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_start=12, margin_end=12, margin_top=12, margin_bottom=12)
        self._dock = DockConfig()
        card = SettingsCard(title="Dock")
        self.append(card)

        # Position ----------------------------------------------------------
        position_combo = Gtk.ComboBoxText()
        self.position_combo = position_combo
        for pos in ["bottom", "left", "right", "top"]:
            position_combo.append_text(pos)
        position_combo.set_active_id(self._dock.get_position())
        position_combo.connect("changed", self._on_position_changed)
        card.add(SettingsRow("Position", widget=position_combo))

        # Icon size ----------------------------------------------------------
        size_adj = Gtk.Adjustment(value=self._dock.get_icon_size(), lower=16, upper=128, step_increment=4)
        size_spin = Gtk.SpinButton(adjustment=size_adj, climb_rate=1.0, digits=0)
        self.size_spin = size_spin
        size_spin.connect("value-changed", self._on_icon_size_changed)
        card.add(SettingsRow("Icon size", widget=size_spin))

        # Zoom ---------------------------------------------------------------
        zoom_adj = Gtk.Adjustment(value=self._dock.get_zoom(), lower=0.5, upper=2.0, step_increment=0.1)
        zoom_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=zoom_adj)
        self.zoom_scale = zoom_scale
        zoom_scale.set_digits(2)
        zoom_scale.set_hexpand(True)
        zoom_scale.connect("value-changed", self._on_zoom_changed)
        card.add(SettingsRow("Zoom", widget=zoom_scale))

        # Transparency -------------------------------------------------------
        trans_adj = Gtk.Adjustment(value=self._dock.get_transparency(), lower=0.0, upper=1.0, step_increment=0.05)
        trans_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=trans_adj)
        self.trans_scale = trans_scale
        trans_scale.set_digits(2)
        trans_scale.set_hexpand(True)
        trans_scale.connect("value-changed", self._on_transparency_changed)
        card.add(SettingsRow("Transparency", widget=trans_scale))

        # Autohide -----------------------------------------------------------
        autohide_switch = Gtk.Switch()
        self.autohide_switch = autohide_switch
        autohide_switch.set_active(self._dock.get_autohide())
        autohide_switch.connect("state-set", self._on_autohide_toggled)
        card.add(SettingsRow("Auto‑hide", widget=autohide_switch))

        # Spacing -----------------------------------------------------------
        spacing_adj = Gtk.Adjustment(value=self._dock.get_spacing(), lower=0, upper=20, step_increment=1)
        spacing_spin = Gtk.SpinButton(adjustment=spacing_adj, climb_rate=1.0, digits=0)
        self.spacing_spin = spacing_spin
        spacing_spin.connect("value-changed", self._on_spacing_changed)
        card.add(SettingsRow("Spacing", widget=spacing_spin))

        # Animation speed ----------------------------------------------------
        anim_adj = Gtk.Adjustment(value=self._dock.get_animation_speed(), lower=0.1, upper=3.0, step_increment=0.1)
        anim_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=anim_adj)
        self.anim_scale = anim_scale
        anim_scale.set_digits(2)
        anim_scale.set_hexpand(True)
        anim_scale.connect("value-changed", self._on_animation_speed_changed)
        card.add(SettingsRow("Animation speed", widget=anim_scale))

        # Pinned apps --------------------------------------------------------
        # Card to hold pinned applications list and add button.
        pinned_card = SettingsCard(title="Pinned Apps")
        self.append(pinned_card)

        # ListBox showing current pinned apps.
        self._pinned_listbox = Gtk.ListBox()
        pinned_card.add(self._pinned_listbox)

        # Add Application button – opens a file chooser for .desktop files.
        add_app_button = Gtk.Button(label="Add Application")
        add_app_button.connect("clicked", self._on_add_app_clicked)
        pinned_card.add(SettingsRow("Add App", widget=add_app_button))

        # Populate the list initially.
        self._refresh_pinned_list()

        # Reset button -------------------------------------------------------
        reset_button = Gtk.Button(label="Restore defaults")
        reset_button.get_style_context().add_class("destructive-action")
        reset_button.connect("clicked", self._on_reset_clicked)
        card.add(reset_button)

    # ---------------------------------------------------------------------
    # Callbacks – each writes the new value to the JSON backend.
    # ---------------------------------------------------------------------
    def _on_position_changed(self, combo: Gtk.ComboBoxText) -> None:
        self._dock.set_position(combo.get_active_text() or "bottom")

    def _on_icon_size_changed(self, spin: Gtk.SpinButton) -> None:
        self._dock.set_icon_size(int(spin.get_value()))

    def _on_zoom_changed(self, scale: Gtk.Scale) -> None:
        self._dock.set_zoom(scale.get_value())

    def _on_transparency_changed(self, scale: Gtk.Scale) -> None:
        self._dock.set_transparency(scale.get_value())

    def _on_autohide_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        self._dock.set_autohide(state)
        return False

    def _on_spacing_changed(self, spin: Gtk.SpinButton) -> None:
        self._dock.set_spacing(int(spin.get_value()))

    def _on_animation_speed_changed(self, scale: Gtk.Scale) -> None:
        self._dock.set_animation_speed(scale.get_value())

    def _on_reset_clicked(self, btn: Gtk.Button) -> None:
        # Reset the underlying JSON configuration to its factory defaults
        self._dock.reset_to_defaults()
        # Bring the UI widgets back in sync with the freshly‑loaded defaults
        self.position_combo.set_active_id(self._dock.get_position())
        self.size_spin.set_value(self._dock.get_icon_size())
        self.zoom_scale.set_value(self._dock.get_zoom())
        self.trans_scale.set_value(self._dock.get_transparency())
        self.autohide_switch.set_active(self._dock.get_autohide())
        self.spacing_spin.set_value(self._dock.get_spacing())
        self.anim_scale.set_value(self._dock.get_animation_speed())
        # Refresh pinned apps list UI
        self._refresh_pinned_list()

    # ---------------------------------------------------------------------
    # Pinned apps helpers
    # ---------------------------------------------------------------------
    def _resolve_app_info(self, app_id: str) -> tuple[str, str]:
        """Resolve a GSettings app item/path to (Friendly Name, Icon Name)."""
        clean_id = app_id
        if app_id.startswith("file://"):
            from urllib.parse import urlparse
            try:
                clean_id = pathlib.Path(urlparse(app_id).path).name
            except Exception:
                pass

        if clean_id.endswith(".dockitem"):
            clean_id = clean_id.replace(".dockitem", ".desktop")
        if not clean_id.endswith(".desktop") and not clean_id.startswith("file://"):
            clean_id = clean_id + ".desktop"

        # Search for the desktop file
        for p in [pathlib.Path("/usr/share/applications"), pathlib.Path.home() / ".local" / "share" / "applications"]:
            filepath = p / clean_id
            if filepath.is_file():
                info = parse_desktop_file(filepath)
                return info["name"], info["icon"]

        # Fallback
        name = clean_id
        if name.endswith(".desktop"):
            name = name[:-8]
        return name, ""

    def _refresh_pinned_list(self) -> None:
        """Rebuild the ListBox showing all pinned applications."""
        self._pinned_listbox.remove_all()
        for app in self._dock.get_pinned_apps():
            friendly_name, icon_name = self._resolve_app_info(app)
            row = Gtk.ListBoxRow()
            row.app_id = app
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.set_margin_start(8)
            hbox.set_margin_end(8)
            hbox.set_margin_top(6)
            hbox.set_margin_bottom(6)

            # Icon
            icon = icon_name or "system-run"
            try:
                img = Gtk.Image.new_from_icon_name(icon)
                img.set_pixel_size(24)
                hbox.append(img)
            except Exception:
                pass

            # Name Label (Expands)
            label = Gtk.Label(label=friendly_name)
            label.set_xalign(0)
            label.set_hexpand(True)
            label.set_tooltip_text(app)
            hbox.append(label)

            # Remove Button
            remove_btn = Gtk.Button(label="Remove")
            remove_btn.connect("clicked", self._on_remove_pinned, app)
            hbox.append(remove_btn)

            row.set_child(hbox)

            # Add drag-and-drop controllers for GTK 4
            drag_source = Gtk.DragSource()
            
            def _on_drag_prepare(source, x, y, r=row):
                val = GObject.Value(GObject.TYPE_OBJECT, r)
                return Gdk.ContentProvider.new_for_value(val)
                
            drag_source.connect("prepare", _on_drag_prepare)
            row.add_controller(drag_source)

            drop_target = Gtk.DropTarget.new(GObject.TYPE_OBJECT, Gdk.DragAction.MOVE)
            
            def _on_drop(target, value, x, y, r=row):
                if isinstance(value, Gtk.ListBoxRow) and value != r:
                    listbox = r.get_parent()
                    target_idx = r.get_index()
                    listbox.remove(value)
                    listbox.insert(value, target_idx)
                    self._save_order()
                    return True
                return False
                
            drop_target.connect("drop", _on_drop)
            row.add_controller(drop_target)

            self._pinned_listbox.append(row)

    def _save_order(self) -> None:
        """Traverse the ListBox children to retrieve the new order and update the backend."""
        apps = []
        row_index = 0
        while True:
            row = self._pinned_listbox.get_row_at_index(row_index)
            if row is None:
                break
            if hasattr(row, "app_id"):
                apps.append(row.app_id)
            row_index += 1

        current_apps = self._dock.get_pinned_apps()
        if apps and apps != current_apps:
            self._dock.set_pinned_apps(apps)

    def _on_add_app_clicked(self, button: Gtk.Button) -> None:
        """Open our custom application selector dialog instead of a file chooser."""
        dialog = AppSelectorDialog(self.get_root())
        
        def _on_response(d, response_id):
            if response_id == Gtk.ResponseType.ACCEPT:
                selected_row = d.listbox.get_selected_row()
                if selected_row and hasattr(selected_row, "app_data"):
                    app = selected_row.app_data
                    self._dock.add_pinned_app(app["id"])
                    self._refresh_pinned_list()
            d.destroy()

        dialog.connect("response", _on_response)
        dialog.show()

    def _on_remove_pinned(self, button: Gtk.Button, app: str) -> None:
        """Remove *app* from the pinned apps list and update UI."""
        self._dock.remove_pinned_app(app)
        self._refresh_pinned_list()


def parse_desktop_file(filepath: pathlib.Path) -> dict:
    """Parse a .desktop file to extract its Name and Icon."""
    info = {"name": filepath.name, "icon": "", "id": filepath.name}
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            in_group = False
            for line in f:
                line = line.strip()
                if line == "[Desktop Entry]":
                    in_group = True
                elif line.startswith("[") and line.endswith("]"):
                    in_group = False
                elif in_group and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if key == "Name":
                        info["name"] = val
                    elif key == "Icon":
                        info["icon"] = val
    except Exception:
        pass
    return info


def get_installed_apps() -> list[dict]:
    """Find and return all installed applications' info sorted by Name."""
    apps = []
    seen_ids = set()
    paths = [
        pathlib.Path("/usr/share/applications"),
        pathlib.Path.home() / ".local" / "share" / "applications"
    ]
    for p in paths:
        if p.is_dir():
            for filepath in p.glob("*.desktop"):
                if filepath.name in seen_ids:
                    continue
                seen_ids.add(filepath.name)
                info = parse_desktop_file(filepath)
                apps.append(info)
    apps.sort(key=lambda x: x["name"].lower())
    return apps


class AppSelectorDialog(Gtk.Dialog):
    """Custom popup dialog to select an application from a list of installed apps."""

    def __init__(self, parent: Gtk.Window) -> None:
        super().__init__(title="Select Application", transient_for=parent, modal=True)
        self.set_default_size(400, 500)

        content = self.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)

        # Search box
        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Search applications...")
        search_entry.connect("search-changed", self._on_search_changed)
        content.append(search_entry)

        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        content.append(scrolled)

        # List box for applications
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self._on_row_selected)
        scrolled.set_child(self.listbox)

        # Add buttons to action area
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.select_button = self.add_button("Select", Gtk.ResponseType.ACCEPT)
        self.select_button.get_style_context().add_class("suggested-action")
        self.select_button.set_sensitive(False)

        # Populate list
        self.all_apps = get_installed_apps()
        self._populate_list("")

    def _populate_list(self, filter_text: str) -> None:
        # Clear list box
        while True:
            row = self.listbox.get_row_at_index(0)
            if row is None:
                break
            self.listbox.remove(row)

        filter_text = filter_text.lower()
        for app in self.all_apps:
            if filter_text and filter_text not in app["name"].lower():
                continue

            row = Gtk.ListBoxRow()
            row.app_data = app

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_start(8)
            box.set_margin_end(8)
            box.set_margin_top(8)
            box.set_margin_bottom(8)

            # Icon
            icon_name = app["icon"] or "system-run"
            try:
                img = Gtk.Image.new_from_icon_name(icon_name)
                img.set_pixel_size(24)
                box.append(img)
            except Exception:
                pass

            label = Gtk.Label(label=app["name"])
            label.set_xalign(0)
            box.append(label)

            row.set_child(box)
            self.listbox.append(row)

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self._populate_list(entry.get_text())

    def _on_row_selected(self, listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        self.select_button.set_sensitive(row is not None)
