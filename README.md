# SentinX Control Center – Dock Enhancements

## Overview
This repository contains the **SentinX Control Center**, a GTK 4 based configuration UI for the **SentinX Dock** (Plank). The recent work focuses on extending dock management capabilities and improving reliability.

---

## What Has Been Implemented

### 1. Robust Dock Settings Backend (`backend/dock.py`)
- **JSON + GSettings sync** – All dock preferences are stored in `~/.config/sentinx/dock.json` **and** mirrored to Plank’s GSettings schema (`net.launchpad.plank.dock.settings`).
- **Autohide synchronization** – On startup the current GSettings `hide‑mode` is read and the JSON `autohide` flag is updated, ensuring the UI always reflects the real dock state.
- **Icon‑size validation** – `set_icon_size` now clamps values to the schema‑valid range (24‑128) before persisting, preventing GSettings errors.
- **Pinned‑apps handling** –
  - `get_pinned_apps` reads from GSettings `dock-items` (fallback to JSON).
  - `set_pinned_apps` writes to both GSettings and JSON.
  - Convenience helpers `add_pinned_app` / `remove_pinned_app` added for UI use.
- **Reset to defaults** – Resets the JSON configuration **and** forces all GSettings keys (position, size, zoom, autohide, spacing, animation speed, and pinned apps) back to factory defaults, then reloads the XML tree.

### 2. Dock Page UI (`pages/dock.py`)
- Added a **Pinned Apps** card that shows currently pinned applications in a `Gtk.ListBox`.
- **Add Application** button opens a native GTK 4 `Gtk.FileChooserNative` filtered for `*.desktop` files, adds the selected app to the pinned list, and refreshes the UI.
- Each list row includes a **Remove** button to unpin an app.
- Reset button now also refreshes the pinned‑apps list.
- Updated `_refresh_pinned_list`, `_on_add_app_clicked`, and `_on_remove_pinned` to work with the new backend methods.

### 3. Appearance Page Fix (`pages/appearance.py`)
- Replaced the deprecated `Gtk.FileChooserDialog` with `Gtk.FileChooserNative` for wallpaper selection.
- Added safe fallback handling for the missing `run()` method and an image‑file filter.

### 4. General Improvements
- Added missing imports (`pathlib`) where required.
- Ensured all UI dialogs use `transient_for=self.get_root()` (GTK 4) instead of the removed `get_toplevel()`.
- Added comprehensive inline documentation/comments.

---

## How to Use
1. **Run the Control Center**
   ```bash
   cd /home/danny/Desktop/SentinX-OS/Sentinel-Dock/source/sentinx-control-center
   python3 main.py
   ```
   - The Dock page now includes a section to manage pinned apps.
   - Changes to position, size, zoom, autohide, etc., are instantly reflected in the running Plank dock.

2. **Add a Pinned App**
   - Click **Add Application**, choose a `.desktop` file, and the app appears in the list and on the dock.
   - Use the **Remove** button next to any entry to unpin it.

3. **Reset Settings**
   - Press **Restore defaults** to revert all dock settings (including pinned apps) to the original configuration.

---

## Development & Contribution
- The project follows the standard Git workflow. After making changes run:
  ```bash
  git add source/sentinx-control-center/README.md
  git add <modified files>
  git commit -m "Enhanced dock backend, added pinned‑apps UI, fixed dialogs"
  git push origin main
  ```
- Ensure you have the latest Plank GSettings schema compiled:
  ```bash
  glib-compile-schemas /home/danny/Desktop/SentinX-OS/Sentinel-Dock/source/sentinx-dock/data
  ```

---

## License
The code is released under the same license as the rest of the Sentinel‑Dock project (see the top‑level `LICENSE` file).

---

*Last updated: $(date '+%Y-%m-%d')*
