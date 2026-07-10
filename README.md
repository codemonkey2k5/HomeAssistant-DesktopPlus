# DesktopPlus

**DesktopPlus** is a free Windows desktop panel that opens any web dashboard (Home Assistant or other) as a borderless, always-available display on a chosen monitor.

It is designed to feel like a live desktop background: full usable screen, taskbar left visible when present, fully interactive, never forced always-on-top.

Repository: [codemonkey2k5/HomeAssistant-DesktopPlus](https://github.com/codemonkey2k5/HomeAssistant-DesktopPlus)

---

## Features

| Feature | Description |
|--------|-------------|
| **Any URL** | Home Assistant, Grafana, or any web page — set on first run or from the tray |
| **Multi-monitor** | Pick display 1..N from the system tray; sizes come from Windows, not hard-coded pixels |
| **Work area / kiosk** | **Normal mode** fills the work area (leaves the taskbar). **Kiosk mode** fills the full monitor |
| **Auto-refresh** | Configurable interval (default 10 minutes); refresh now from the tray |
| **Scroll control** | Hide scrollbars and/or disable scrolling for a clean wall/dashboard look |
| **Window chrome** | Frameless, resizable, drag, always-on-top (some options apply after restart) |
| **System tray** | All settings in one place; no need to edit code for day-to-day use |
| **Mixed DPI safe** | Correct placement when monitors use different scaling (e.g. 175% + 100%) |

---

## Requirements

- **Windows 10 or 11**
- **Python 3.11+** (3.13 works; the Python that opens `.pyw` must have the packages installed)
- **Microsoft Edge WebView2 Runtime** (usually already installed on Windows 11; free download from Microsoft if needed)
- Free packages: `pywebview`, `pystray`, `Pillow`

---

## Install

1. Install [Python](https://www.python.org/downloads/) if needed.  
   During setup, enable **“Add python.exe to PATH”** if offered.

2. Open a terminal in this folder and install dependencies for the Python that will run the app:

   ```bat
   py -m pip install -r requirements.txt
   ```

   If double-click still fails with a missing-module message, install for that exact interpreter:

   ```bat
   py -3.13 -m pip install -r requirements.txt
   ```

3. Double-click **`DesktopPlus.pyw`**.

4. On first run, enter your dashboard URL (example):

   ```text
   http://homeassistant.local:8123/lovelace/0
   ```

5. Optional: right-click `DesktopPlus.pyw` → **Show more options** → **Send to** → **Desktop (create shortcut)**, then add the shortcut to Startup if you want it at login.

---

## System tray

Right-click the DesktopPlus tray icon (monitor with colored tiles):

- **Refresh now** / **Re-apply layout**
- **Set dashboard URL…**
- **Auto-refresh** and **Refresh interval**
- **Display** — live list of monitors (size, work area, taskbar note)
- **Fit work area (normal mode)** — off = kiosk / full monitor
- Scrolling / scrollbars
- Frameless / resizable / allow move (restart to apply)
- Always on top
- Open config folder / Quit

Settings are stored in `config.json` next to the script (created automatically).

---

## Config file

`config.json` example fields:

```json
{
  "url": "http://homeassistant.local:8123/lovelace/0",
  "display_index": 0,
  "fit_work_area": true,
  "refresh_enabled": true,
  "refresh_interval_seconds": 600,
  "scrolling_enabled": false,
  "show_scrollbars": false,
  "frameless": true,
  "resizable": false,
  "on_top": false,
  "allow_move": false,
  "private_mode": false,
  "window_title": "DesktopPlus"
}
```

You do **not** set screen coordinates manually. Geometry is always computed from the selected monitor.

---

## Troubleshooting

| Problem | What to try |
|--------|-------------|
| Double-click does nothing | Run `run_debug.bat`, or check `desktopplus.log`. Install packages for the Python that `pyw` uses (`py -0p`). |
| Missing module error | `py -m pip install -r requirements.txt` |
| Blank / WebView error | Install [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) |
| Wrong monitor / off-screen | Tray → **Display** → pick the screen; **Re-apply layout** |
| Edge hairline on second monitor | Fixed in v2 (overscan + no shadow). Update to latest release. |

---

## Files

| File | Purpose |
|------|---------|
| `DesktopPlus.pyw` | Launcher — **double-click this** to run |
| `desktopplus_core.py` | Monitors, config, window placement |
| `desktopplus_ui.py` | Tray menu, webview window, main loop |
| `requirements.txt` | Python dependencies |
| `tray_icon.png` | Tray icon (auto-created if missing) |
| `run_debug.bat` | Console launch for diagnosing errors |
| `config.json` | Local settings (created at runtime; not in git) |
| `desktopplus.log` | Local log (created at runtime; not in git) |

Keep `DesktopPlus.pyw`, `desktopplus_core.py`, and `desktopplus_ui.py` in the **same folder**.

---

## Version

**2.0.0** — full rewrite: multi-monitor work-area placement, system tray UI, URL configuration, mixed-DPI fixes, scroll options.

---

## License

Use and modify freely for personal or community Home Assistant / dashboard setups. Please keep attribution to the project when redistributing.
