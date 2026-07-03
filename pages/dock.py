# -*- coding: utf-8 -*-
"""Dock configuration page – premium UI, drag-and-drop pinned apps reordering."""

from __future__ import annotations
import pathlib
from gi.repository import Gtk, Gdk, GObject

from backend.dock import DockConfig
from widgets.card import SettingsCard
from widgets.setting_row import SettingsRow


class DockPage(Gtk.Box):
    """Premium page for dock preferences."""

    def __init__(self) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=0,
            margin_start=24, margin_end=24, margin_top=24, margin_bottom=24
        )
        self._dock = DockConfig()

        # ── Page header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_bottom(20)
        t = Gtk.Label(label="Dock")
        t.set_xalign(0)
        t.get_style_context().add_class("page-title")
        header.append(t)
        st = Gtk.Label(label="Configure the SentinX application dock")
        st.set_xalign(0)
        st.get_style_context().add_class("page-subtitle")
        header.append(st)
        self.append(header)

        # ── Layout card
        layout_card = SettingsCard(title="Layout", icon_name="go-bottom-symbolic")

        position_combo = Gtk.ComboBoxText()
        self.position_combo = position_combo
        for pos in ["bottom", "left", "right", "top"]:
            position_combo.append_text(pos)
        position_combo.set_active_id(self._dock.get_position())
        position_combo.connect("changed", self._on_position_changed)
        layout_card.add(SettingsRow("Position", subtitle="Which screen edge the dock appears on", widget=position_combo))

        size_adj = Gtk.Adjustment(value=self._dock.get_icon_size(), lower=16, upper=128, step_increment=4)
        size_spin = Gtk.SpinButton(adjustment=size_adj, climb_rate=1.0, digits=0)
        self.size_spin = size_spin
        size_spin.connect("value-changed", self._on_icon_size_changed)
        layout_card.add(SettingsRow("Icon Size", subtitle="Size of dock icons in pixels", widget=size_spin))

        zoom_adj = Gtk.Adjustment(value=self._dock.get_zoom(), lower=0.5, upper=2.0, step_increment=0.1)
        zoom_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=zoom_adj)
        self.zoom_scale = zoom_scale
        zoom_scale.set_digits(2)
        zoom_scale.set_hexpand(True)
        zoom_scale.connect("value-changed", self._on_zoom_changed)
        layout_card.add(SettingsRow("Zoom Factor", subtitle="Magnification on mouse hover", widget=zoom_scale))

        spacing_adj = Gtk.Adjustment(value=self._dock.get_spacing(), lower=0, upper=20, step_increment=1)
        spacing_spin = Gtk.SpinButton(adjustment=spacing_adj, climb_rate=1.0, digits=0)
        self.spacing_spin = spacing_spin
        spacing_spin.connect("value-changed", self._on_spacing_changed)
        layout_card.add(SettingsRow("Item Spacing", subtitle="Gap between icons in pixels", widget=spacing_spin))

        self.append(layout_card)

        # ── Behaviour card
        behav_card = SettingsCard(title="Behaviour", icon_name="system-run-symbolic")

        autohide_switch = Gtk.Switch()
        self.autohide_switch = autohide_switch
        autohide_switch.set_active(self._dock.get_autohide())
        autohide_switch.connect("state-set", self._on_autohide_toggled)
        behav_card.add(SettingsRow("Auto-Hide", subtitle="Hide dock when a window overlaps it", widget=autohide_switch))

        trans_adj = Gtk.Adjustment(value=self._dock.get_transparency(), lower=0.0, upper=1.0, step_increment=0.05)
        trans_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=trans_adj)
        self.trans_scale = trans_scale
        trans_scale.set_digits(2)
        trans_scale.set_hexpand(True)
        trans_scale.connect("value-changed", self._on_transparency_changed)
        behav_card.add(SettingsRow("Transparency", subtitle="Background transparency of the dock", widget=trans_scale))

        anim_adj = Gtk.Adjustment(value=self._dock.get_animation_speed(), lower=0.1, upper=3.0, step_increment=0.1)
        anim_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=anim_adj)
        self.anim_scale = anim_scale
        anim_scale.set_digits(2)
        anim_scale.set_hexpand(True)
        anim_scale.connect("value-changed", self._on_animation_speed_changed)
        behav_card.add(SettingsRow("Animation Speed", subtitle="Speed of hover zoom / bounce animations", widget=anim_scale))

        self.append(behav_card)

        # ── Pinned Apps card
        pinned_card = SettingsCard(title="Pinned Applications", icon_name="view-list-symbolic")

        hint = Gtk.Label(label="Drag rows to reorder • Click Remove to unpin")
        hint.get_style_context().add_class("setting-subtitle")
        hint.set_xalign(0)
        hint.set_margin_start(20)
        hint.set_margin_top(4)
        hint.set_margin_bottom(8)
        pinned_card.add(hint)

        self._pinned_listbox = Gtk.ListBox()
        self._pinned_listbox.set_margin_start(12)
        self._pinned_listbox.set_margin_end(12)
        self._pinned_listbox.set_margin_bottom(8)
        pinned_card.add(self._pinned_listbox)

        add_btn = Gtk.Button(label="＋  Add Application")
        add_btn.get_style_context().add_class("action-button")
        add_btn.set_halign(Gtk.Align.START)
        add_btn.set_margin_start(20)
        add_btn.set_margin_bottom(16)
        add_btn.connect("clicked", self._on_add_app_clicked)
        pinned_card.add(add_btn)

        self.append(pinned_card)
        self._refresh_pinned_list()

        # ── Reset card
        reset_card = SettingsCard(title="Reset", icon_name="edit-undo-symbolic")
        reset_btn = Gtk.Button(label="Restore Default Settings")
        reset_btn.get_style_context().add_class("destructive-action")
        reset_btn.set_margin_start(20)
        reset_btn.set_margin_end(20)
        reset_btn.set_margin_top(8)
        reset_btn.set_margin_bottom(16)
        reset_btn.connect("clicked", self._on_reset_clicked)
        reset_card.add(reset_btn)
        self.append(reset_card)

    # ─────────────────────────────────────────────────────────
    # Setting callbacks
    # ─────────────────────────────────────────────────────────
    def _on_position_changed(self, combo):
        self._dock.set_position(combo.get_active_text() or "bottom")

    def _on_icon_size_changed(self, spin):
        self._dock.set_icon_size(int(spin.get_value()))

    def _on_zoom_changed(self, scale):
        self._dock.set_zoom(scale.get_value())

    def _on_transparency_changed(self, scale):
        self._dock.set_transparency(scale.get_value())

    def _on_autohide_toggled(self, switch, state):
        self._dock.set_autohide(state)
        return False

    def _on_spacing_changed(self, spin):
        self._dock.set_spacing(int(spin.get_value()))

    def _on_animation_speed_changed(self, scale):
        self._dock.set_animation_speed(scale.get_value())

    def _on_reset_clicked(self, btn):
        self._dock.reset_to_defaults()
        self.position_combo.set_active_id(self._dock.get_position())
        self.size_spin.set_value(self._dock.get_icon_size())
        self.zoom_scale.set_value(self._dock.get_zoom())
        self.trans_scale.set_value(self._dock.get_transparency())
        self.autohide_switch.set_active(self._dock.get_autohide())
        self.spacing_spin.set_value(self._dock.get_spacing())
        self.anim_scale.set_value(self._dock.get_animation_speed())
        self._refresh_pinned_list()

    # ─────────────────────────────────────────────────────────
    # Pinned apps
    # ─────────────────────────────────────────────────────────
    def _resolve_app_info(self, app_id: str) -> tuple[str, str]:
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
            clean_id += ".desktop"

        for p in [pathlib.Path("/usr/share/applications"),
                  pathlib.Path.home() / ".local" / "share" / "applications"]:
            fp = p / clean_id
            if fp.is_file():
                info = parse_desktop_file(fp)
                return info["name"], info["icon"]

        name = clean_id
        if name.endswith(".desktop"):
            name = name[:-8]
        return name, ""

    def _refresh_pinned_list(self) -> None:
        self._pinned_listbox.remove_all()
        for app in self._dock.get_pinned_apps():
            friendly_name, icon_name = self._resolve_app_info(app)
            row = Gtk.ListBoxRow()
            row.app_id = app

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.get_style_context().add_class("pinned-app-row")
            hbox.set_hexpand(True)

            # Drag handle
            grip = Gtk.Label(label="⠿")
            grip.get_style_context().add_class("drag-handle")
            hbox.append(grip)

            # Icon
            icon = icon_name or "system-run"
            try:
                img = Gtk.Image.new_from_icon_name(icon)
                img.set_pixel_size(24)
                hbox.append(img)
            except Exception:
                pass

            # Name label
            lbl = Gtk.Label(label=friendly_name)
            lbl.set_xalign(0)
            lbl.set_hexpand(True)
            lbl.set_tooltip_text(app)
            lbl.get_style_context().add_class("setting-title")
            hbox.append(lbl)

            # Remove button
            rm_btn = Gtk.Button(label="Remove")
            rm_btn.get_style_context().add_class("destructive-action")
            rm_btn.connect("clicked", self._on_remove_pinned, app)
            hbox.append(rm_btn)

            row.set_child(hbox)

            # GTK4 drag-and-drop
            drag_source = Gtk.DragSource()

            def _on_prepare(source, x, y, r=row):
                return Gdk.ContentProvider.new_for_value(GObject.Value(GObject.TYPE_OBJECT, r))

            drag_source.connect("prepare", _on_prepare)
            row.add_controller(drag_source)

            drop_target = Gtk.DropTarget.new(GObject.TYPE_OBJECT, Gdk.DragAction.MOVE)

            def _on_drop(target, value, x, y, r=row):
                if isinstance(value, Gtk.ListBoxRow) and value != r:
                    lb = r.get_parent()
                    idx = r.get_index()
                    lb.remove(value)
                    lb.insert(value, idx)
                    self._save_order()
                    return True
                return False

            drop_target.connect("drop", _on_drop)
            row.add_controller(drop_target)

            self._pinned_listbox.append(row)

    def _save_order(self) -> None:
        apps, i = [], 0
        while True:
            row = self._pinned_listbox.get_row_at_index(i)
            if row is None:
                break
            if hasattr(row, "app_id"):
                apps.append(row.app_id)
            i += 1
        current = self._dock.get_pinned_apps()
        if apps and apps != current:
            self._dock.set_pinned_apps(apps)

    def _on_add_app_clicked(self, btn) -> None:
        dialog = AppSelectorDialog(self.get_root())

        def _on_response(d, resp):
            if resp == Gtk.ResponseType.ACCEPT:
                sel = d.listbox.get_selected_row()
                if sel and hasattr(sel, "app_data"):
                    self._dock.add_pinned_app(sel.app_data["id"])
                    self._refresh_pinned_list()
            d.destroy()

        dialog.connect("response", _on_response)
        dialog.show()

    def _on_remove_pinned(self, btn, app) -> None:
        self._dock.remove_pinned_app(app)
        self._refresh_pinned_list()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def parse_desktop_file(filepath: pathlib.Path) -> dict:
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
                    key, val = key.strip(), val.strip()
                    if key == "Name":
                        info["name"] = val
                    elif key == "Icon":
                        info["icon"] = val
    except Exception:
        pass
    return info


def get_installed_apps() -> list[dict]:
    apps, seen = [], set()
    for p in [pathlib.Path("/usr/share/applications"),
              pathlib.Path.home() / ".local" / "share" / "applications"]:
        if p.is_dir():
            for fp in p.glob("*.desktop"):
                if fp.name not in seen:
                    seen.add(fp.name)
                    apps.append(parse_desktop_file(fp))
    apps.sort(key=lambda x: x["name"].lower())
    return apps


class AppSelectorDialog(Gtk.Dialog):
    """Searchable application selector popup."""

    def __init__(self, parent: Gtk.Window) -> None:
        super().__init__(title="Add Application", transient_for=parent, modal=True)
        self.set_default_size(440, 540)

        content = self.get_content_area()
        content.set_spacing(0)

        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        wrapper.set_margin_start(16)
        wrapper.set_margin_end(16)
        wrapper.set_margin_top(16)
        wrapper.set_margin_bottom(12)
        content.append(wrapper)

        title_lbl = Gtk.Label(label="Select Application to Pin")
        title_lbl.get_style_context().add_class("page-title")
        title_lbl.set_xalign(0)
        wrapper.append(title_lbl)

        search = Gtk.SearchEntry()
        search.set_placeholder_text("Search installed applications…")
        search.connect("search-changed", self._on_search)
        wrapper.append(search)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        wrapper.append(scroll)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self._on_row_selected)
        scroll.set_child(self.listbox)

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self._select_btn = self.add_button("Pin Application", Gtk.ResponseType.ACCEPT)
        self._select_btn.get_style_context().add_class("suggested-action")
        self._select_btn.set_sensitive(False)

        self.all_apps = get_installed_apps()
        self._populate("")

    def _populate(self, text: str) -> None:
        self.listbox.remove_all()
        text = text.lower()
        for app in self.all_apps:
            if text and text not in app["name"].lower():
                continue
            row = Gtk.ListBoxRow()
            row.app_data = app

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_start(12)
            box.set_margin_end(12)
            box.set_margin_top(10)
            box.set_margin_bottom(10)

            try:
                img = Gtk.Image.new_from_icon_name(app["icon"] or "system-run")
                img.set_pixel_size(28)
                box.append(img)
            except Exception:
                pass

            lbl = Gtk.Label(label=app["name"])
            lbl.set_xalign(0)
            lbl.get_style_context().add_class("setting-title")
            box.append(lbl)

            row.set_child(box)
            self.listbox.append(row)

    def _on_search(self, entry):
        self._populate(entry.get_text())

    def _on_row_selected(self, lb, row):
        self._select_btn.set_sensitive(row is not None)
