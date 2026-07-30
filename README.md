# DesktopPlus

**DesktopPlus** shows your Home Assistant dashboard (or any web page) on one of your computer screens.

It is meant to look like a **live desktop background**:

- Fills the screen you choose  
- Leaves the Windows taskbar visible (when that screen has one)  
- Still clickable and fully usable  
- Does **not** stay stuck on top of other programs (unless you turn on Always on top)  
- **No DesktopPlus button on the Windows taskbar** — use the **system tray** icon only  

**Current version: 2.2.0**  
**Works on:** Windows 10 and Windows 11  
**Cost:** Free  

**Upgrading from 2.0 / 2.1 / 2.1.1:**  
Download the new **DesktopPlus.exe**, put it in your folder, and **keep your old `config.json`** next to it. Your dashboard URL stays in that file — you should **not** need to type it again.

Project page: https://github.com/codemonkey2k5/HomeAssistant-DesktopPlus  

---

## What’s new (2.2.0)

1. **No Python install** — download one program file and run it.  
2. **No button on the Windows taskbar** — use the small tray icon near the clock.  
3. **Start on login** — a tray checkbox starts DesktopPlus when you sign in to Windows.  
4. **Help…** and **About…** in the tray menu, with multi-screen instructions.  
5. Works with **any web address**, not only Home Assistant (for example `google.com` or your dashboard).  
6. Clearer tray menu; improved icon for shortcuts.  
7. Tray settings that do not need a restart apply right away (including a page reload when needed).  
8. Built on the reliability work from version 2.1.1 (refresh, tray, layout, log cleanup).  
9. Upgrading keeps your saved URL if you keep (or copy) `config.json` — no need to type it again.  

More history: see **CHANGELOG.md**.

---

## Quick answers

### Do I need Python?

**No.** Version 2.2 is a single **DesktopPlus.exe**. Double-click it and go.

### What is `.gitignore`?

You can **ignore this file** for day-to-day use. You never open it to run DesktopPlus.

It is only for people who put the project on GitHub (or use git). It tells git:  
“Don’t upload my personal settings or log files.”

**Beginners:** leave `.gitignore` in the folder (if you have one) and don’t worry about it.

### Where is the tray icon?

The tray icon is the small picture near the **clock** (bottom-right of Windows). If you don’t see it, click the **^** arrow to show hidden icons.

---

## What you need before installing

1. A **Windows 10 or Windows 11** computer  
2. Your **Home Assistant address** (or any website address you want on the screen)  
   Example shape (yours will be different):  
   `http://homeassistant.local:8123/lovelace/0`  
3. A few minutes  

You do **not** need to know how to program.  
You do **not** need to install Python.

---

# Install (new users — start here)

Follow these steps **in order**.

---

### Step 1 — Download DesktopPlus

1. Open this page in your web browser:  
   https://github.com/codemonkey2k5/HomeAssistant-DesktopPlus/releases  
2. Click the latest release (**DesktopPlus v2.2.0**).  
3. Under **Assets**, download **`DesktopPlus.exe`**.  
4. Create a simple folder, for example:  
   `C:\DesktopPlus`  
5. Move **DesktopPlus.exe** into that folder.

That’s it for files. You only need the one program file to start.

---

### Step 2 — Start DesktopPlus

1. Double-click **`DesktopPlus.exe`**.  
2. The first time, a small box should ask for a **URL** (web address).  
3. Type or paste your address. Examples:

```text
http://homeassistant.local:8123/lovelace/0
google.com
https://example.com
```

   - You can leave off `http://` — if you type something like `google.com`, DesktopPlus adds `http://` for you.  
   - Prefer `https://` when the site needs it.  

4. Click **OK**.  
5. A window should open with your page.  
6. Look near the Windows clock for the DesktopPlus tray icon.  
   - Click **^** if icons are hidden.

**Tip:** Your settings are saved in a file named **`config.json`** in the same folder. It is created automatically. The log file is **`desktopplus.log`** (it stays small and cleans itself up).

---

### Step 3 — Put it on the correct screen (if you have more than one)

1. **Right-click** the DesktopPlus tray icon.  
2. Open **Display**.  
3. Click the screen you want (Screen 1, Screen 2, etc.).  
4. The window should move there right away.

**Tip:**  
- **Fit work area (normal mode)** = checked → leaves the taskbar visible when that screen has one.  
- Unchecked = **kiosk mode** (fills the whole screen; may cover the taskbar on that screen).

---

### Step 4 — Optional: start automatically when Windows starts

1. Right-click the DesktopPlus tray icon.  
2. Check **Start on login**.  
3. Uncheck anytime to remove it from startup.

---

# Upgrade from an older version

### From 2.0 / 2.1 / 2.1.1 (Python / script version)

1. **Quit** the old DesktopPlus if it is running.  
2. Download **DesktopPlus.exe** from the new release (Install → Step 1).  
3. Put **DesktopPlus.exe** in a folder (a new folder or your old one).  
4. **Copy your old `config.json`** into the same folder as the new exe (if you still have it).  
5. Double-click **DesktopPlus.exe**.  
6. You should **not** need to type your URL again if `config.json` came along.  
7. You can stop using the old `.pyw` files and Python install steps for DesktopPlus.

### From version 1.0

Version **1.0** was a single script (often **`HAD-PLus.pyw`**).  
Use the **Install** steps above for 2.2, then enter your dashboard URL once when asked.  
Use the tray menu → **Display** to pick your screen (this replaces the old hard-coded position/size).

---

# Using more than one screen

Each running DesktopPlus controls **one** screen (one panel + one tray icon).

### Easiest way — two folders

1. Make two folders, for example:  
   `C:\DesktopPlus-Screen1`  
   `C:\DesktopPlus-Screen2`  
2. Put a copy of **DesktopPlus.exe** in each folder.  
3. Run the first copy → **Display** → Screen 1 → set the URL.  
4. Run the second copy → **Display** → Screen 2 → set that URL.  
5. Each folder gets its own `config.json`, so they do not overwrite each other.  
6. Turn on **Start on login** in each copy if you want both to start at sign-in.

### Advanced — one folder, two config files

```text
DesktopPlus.exe --config config-screen2.json
```

Do **not** run two copies that both use the same `config.json`.

---

# Using the tray menu (after it is running)

**Right-click** the DesktopPlus icon near the clock:

| Menu item | What it does |
|-----------|----------------|
| **Refresh now** | Reloads the page immediately |
| **Re-apply layout** | Re-sizes/re-positions to the selected screen |
| **Set URL…** | Change the web address |
| **Auto-refresh** | Turn timed reload on/off |
| **Refresh interval** | How often it reloads (5 / 10 / 15 / 30 / 60 minutes) |
| **Display** | Which monitor to use |
| **Fit work area (normal mode)** | On = leave taskbar; Off = full monitor kiosk |
| **Scrolling / scrollbars** | Allow or block page scrolling |
| **Frameless / Resizable / Allow move** | Window border and drag options (**restart required**) |
| **Always on top** | Keep above other windows (usually leave **off**) |
| **Start on login** | Start this copy when you sign in to Windows |
| **Open config folder** | Opens the folder with your settings and log |
| **Help…** | Full in-app instructions |
| **About…** | Version and file paths |
| **Quit** | Closes DesktopPlus |

Most options apply right away. Only **Frameless**, **Resizable**, and **Allow move** need you to quit and start again.

---

# If something goes wrong

### Double-click does nothing / program won’t start

1. Make sure you downloaded **DesktopPlus.exe** from the **Releases** page (not only Source code).  
2. Try right-click → **Run as administrator** only if your PC policy blocks normal runs (usually not needed).  
3. Look for **`desktopplus.log`** in the same folder and open it with Notepad.  

### Blank window or browser error

Install Microsoft’s free **WebView2** component:  
https://developer.microsoft.com/microsoft-edge/webview2/  

On many Windows 11 PCs it is already installed.

### Wrong screen / window off-screen

Tray icon → **Display** → pick the correct screen → **Re-apply layout**.

### I moved only the .exe and it used to need a big folder

Version **2.2** is a **single file**. You no longer need an `_internal` folder or Python files next to it.  
Keep **DesktopPlus.exe** and (if you have one) **config.json** in the same folder.

### Still stuck?

Open an Issue here and describe what you clicked and what you saw:  
https://github.com/codemonkey2k5/HomeAssistant-DesktopPlus/issues  

If you can, attach a screenshot and the text from `desktopplus.log` (do not share passwords).

---

# Files that matter to you

| File name | Do you need it? | What it is |
|-----------|-----------------|------------|
| **DesktopPlus.exe** | **Yes — double-click this to run** | The program (download from Releases) |
| **config.json** | Created automatically | Your personal settings (URL, screen, etc.) |
| **desktopplus.log** | Created automatically | Activity / error log (stays small) |
| **README.md** | Optional | These instructions |

---

# Version

**2.2.0** — Standalone program, tray-only, Start on login, Help, any URL. See “What’s new” above.

**2.1.1** — Reliability release (Python/script install).

**2.0** — Full rewrite with tray, multi-monitor, and work-area mode.

**1.0** — Original simple script (`HAD-PLus.pyw`).

---

# License

Free to use and share for personal and Home Assistant community use. Please keep credit to the project if you redistribute it.
