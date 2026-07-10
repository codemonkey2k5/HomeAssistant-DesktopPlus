# DesktopPlus

**DesktopPlus** Turn any website into a clean, borderless desktop window. Fixed position • Auto-refresh • System tray controls • Multi-monitor support. (100% Free)

It is meant to look like a **live desktop background**:

- Fills the screen you choose  
- Leaves the Windows taskbar visible, or you can choose kiosk mode if you want it to go full screen.
- Still clickable and fully usable  
- Does **not** stay stuck on top of other programs unless you want it to.  

**Current version: 2.0**  
**Works on:** Windows 10 and Windows 11  
**Cost:** Free  

Project page: https://github.com/codemonkey2k5/HomeAssistant-DesktopPlus  

---

## Quick answers

### What is `.gitignore`?

You can **ignore this file** for day-to-day use. You never open it to run DesktopPlus.

It is only for people who put the project on GitHub (or use git). It tells git:  
“Don’t upload my personal settings or log files.”  

Examples of things it keeps private:

- Your dashboard address (`config.json`)  
- Log files  

**Beginners:** leave `.gitignore` in the folder and don’t worry about it.

### What about the icons?

DesktopPlus can **create the tray icons automatically** the first time it runs (files named `tray_icon.png` and sometimes `tray_icon_256.png`).

They may also be included in the download. Either way is fine.

The tray icon is the small picture near the **clock** (bottom-right of Windows). If you don’t see it, click the **^** arrow to show hidden icons.

---

## What you need before installing

1. A **Windows 10 or Windows 11** computer  
2. Your **Home Assistant address** (or any website address you want on the screen)  
   Example shape (yours will be different):  
   `http://homeassistant.local:8123/lovelace/0`  
3. About **10–15 minutes**

You do **not** need to know how to program.

---

# Install (new users — start here)

Follow these steps **in order**. Do not skip steps.

---

### Step 1 — Download DesktopPlus

1. Open this page in your web browser:  
   https://github.com/codemonkey2k5/HomeAssistant-DesktopPlus/releases  
2. Click the latest release (for example **DesktopPlus v2.0**).  
3. Under **Assets**, download the **Source code (zip)** file.  
   (If you only see a green **Code** button on the main page, click it → **Download ZIP**.)  
4. Find the downloaded zip (usually in your **Downloads** folder).  
5. **Right-click** the zip → **Extract All…** → choose a simple folder, for example:  
   `C:\DesktopPlus`  
6. Click **Extract**.

You should now have a folder that contains at least these files **together**:

- `DesktopPlus.pyw`  
- `desktopplus_core.py`  
- `desktopplus_ui.py`  
- `requirements.txt`  
- `run_debug.bat`  

**Important:** Keep those files in the **same folder**. Do not separate them.

---

### Step 2 — Install Python (the free tool that runs DesktopPlus)

DesktopPlus is a small program written in Python. Windows needs Python installed first.

1. Open: https://www.python.org/downloads/  
2. Click the big yellow button to download Python (any **3.11**, **3.12**, or **3.13** is fine).  
3. Open the installer you downloaded.  
4. **Very important:** On the first screen, turn **ON** the box that says something like:  
   **“Add python.exe to PATH”**  
   (If you skip this, the next steps often fail.)  
5. Click **Install Now**.  
6. When it finishes, click **Close**.  
7. **Restart your computer** (recommended so Windows fully sees Python).

---

### Step 3 — Install the free helper packages

These are free add-ons Python needs (browser window, tray icon, images).

1. Open the folder where you extracted DesktopPlus (example: `C:\DesktopPlus`).  
2. Click once in the **address bar** at the top of File Explorer (where the folder path is shown).  
3. Type `cmd` and press **Enter**.  
   - A black window opens. That is the “Command Prompt.”  
   - It should already be “inside” your DesktopPlus folder.  
4. Copy this line **exactly**, paste it into the black window, then press **Enter**:

```text
py -m pip install -r requirements.txt
```

5. Wait until it finishes (you should get the blinking cursor back with no long red error).  

**If that line fails**, try this instead, then press Enter:

```text
python -m pip install -r requirements.txt
```

**If you still get errors**, copy everything from the black window and ask for help (or open an Issue on the GitHub page).

---

### Step 4 — Start DesktopPlus

1. In your DesktopPlus folder, double-click **`DesktopPlus.pyw`**.  
2. The first time, a small box should ask for a **URL** (web address).  
3. Type or paste your Home Assistant dashboard address, for example:

```text
http://homeassistant.local:8123/lovelace/0
```

4. Click **OK**.  
5. A window should open with your dashboard.  
6. Look near the Windows clock for the DesktopPlus tray icon (monitor with colored tiles).  
   - Click **^** if icons are hidden.

---

### Step 5 — Put it on the correct screen (if you have more than one)

1. **Right-click** the DesktopPlus tray icon.  
2. Open **Display**.  
3. Click the screen you want (Screen 1, Screen 2, etc.).  
4. The window should move there right away.

**Tip:**  
- **Fit work area (normal mode)** = checked → leaves the taskbar visible when that screen has one.  
- Unchecked = **kiosk mode** (fills the whole screen; may cover the taskbar on that screen).

---

### Step 6 — Optional: start automatically when Windows starts

1. Right-click `DesktopPlus.pyw`  
2. Click **Show more options** (Windows 11) if needed  
3. Click **Send to** → **Desktop (create shortcut)**  
4. Press **Windows key + R**, type `shell:startup`, press **Enter**  
5. Drag the DesktopPlus shortcut from your Desktop into that Startup folder  

Now DesktopPlus can start when you sign in to Windows.

---

# Upgrade from version 1.0 (people who already used the old program)

Version **1.0** was a single file (often named something like **`HAD-PLus.pyw`**).  
Version **2.0** is a new folder with several files and a tray menu. You do **not** edit coordinates by hand anymore.

### Upgrade steps (safe)

1. **Close** the old program if it is running  
   - Close the dashboard window, or end it from Task Manager if needed.  
2. **Optional but a good idea:** Copy your old file somewhere safe as a backup  
   - Example: copy `HAD-PLus.pyw` to a folder named `DesktopPlus-backup`.  
3. Download **version 2.0** the same way as **Install → Step 1** (new folder, extract the zip).  
4. Do **Install → Step 2** only if Python is not installed yet.  
   - If Python already works on your PC, skip to Step 5.  
5. Do **Install → Step 3** in the **new** DesktopPlus folder  
   (`py -m pip install -r requirements.txt`).  
6. Double-click **`DesktopPlus.pyw`** in the **new** folder.  
7. Enter your dashboard URL when asked (same address you used before is fine).  
8. Use the tray menu → **Display** to pick your screen (this replaces the old hard-coded position/size).  
9. When you are happy it works, you can delete or ignore the old `HAD-PLus.pyw`.  

### What changed from 1.0 to 2.0 (plain English)

| Old 1.0 | New 2.0 |
|--------|---------|
| One script file | Several files that must stay together |
| Typed screen position numbers in the file | Choose the screen from the tray menu |
| Limited options in code | Most options in the tray menu |
| Refresh often unreliable | Refresh redesigned (default every 10 minutes) |
| No tray menu | System tray menu for settings |

Your old 1.0 settings inside the old `.pyw` file are **not** copied automatically. You set the URL once in 2.0, then use the tray for the rest.

---

# Using the tray menu (after it is running)

**Right-click** the DesktopPlus icon near the clock:

| Menu item | What it does |
|-----------|----------------|
| **Refresh now** | Reloads the page immediately |
| **Re-apply layout** | Re-sizes/re-positions to the selected screen |
| **Set dashboard URL…** | Change the web address |
| **Auto-refresh** | Turn timed reload on/off |
| **Refresh interval** | How often it reloads (5 / 10 / 15 / 30 / 60 minutes) |
| **Display** | Which monitor to use |
| **Fit work area (normal mode)** | On = leave taskbar; Off = full monitor kiosk |
| **Scrolling / scrollbars** | Allow or block page scrolling |
| **Frameless / Resizable / Allow move** | Window border and drag options (some need restart) |
| **Always on top** | Keep above other windows (usually leave **off** for background use) |
| **Open config folder** | Opens the folder with your settings |
| **Quit** | Closes DesktopPlus |

---

# If something goes wrong

### Double-click does nothing

1. Open the DesktopPlus folder.  
2. Double-click **`run_debug.bat`**.  
3. A black window will show messages.  
4. Read the message:  
   - If it says a package is missing → repeat **Install Step 3**.  
   - If it says Python was not found → repeat **Install Step 2** (and check “Add to PATH”).  

Also check for a file named **`desktopplus.log`** in the same folder and open it with Notepad.

### “Missing module” / “No module named webview”

Open Command Prompt **in the DesktopPlus folder** (see Install Step 3) and run:

```text
py -m pip install -r requirements.txt
```

### Blank window or browser error

Install Microsoft’s free **WebView2** component:  
https://developer.microsoft.com/microsoft-edge/webview2/  

On many Windows 11 PCs it is already installed.

### Wrong screen / window off-screen

Tray icon → **Display** → pick the correct screen → **Re-apply layout**.

### Still stuck?

Open an Issue here and describe what you clicked and what you saw:  
https://github.com/codemonkey2k5/HomeAssistant-DesktopPlus/issues  

If you can, attach a screenshot and the text from `desktopplus.log` or `run_debug.bat` (do not share passwords).

---

# Files in the folder (what matters to you)

| File name | Do you need it? | What it is |
|-----------|-----------------|------------|
| **DesktopPlus.pyw** | **Yes — double-click this to run** | Starter program |
| **desktopplus_core.py** | Yes — leave it there | Helper program file |
| **desktopplus_ui.py** | Yes — leave it there | Helper program file |
| **requirements.txt** | Yes — used in install Step 3 | List of free packages to install |
| **run_debug.bat** | Only if something fails | Shows error messages |
| **README.md** | Optional | These instructions |
| **.gitignore** | Optional — ignore it | For GitHub only (see above) |
| **tray_icon.png** | Optional | Icon picture (also auto-created) |
| **config.json** | Created automatically | Your personal settings (URL, screen, etc.) |
| **desktopplus.log** | Created automatically | Error log |

---

# License

Free to use and share for personal and Home Assistant community use. Please keep credit to the project if you redistribute it.
