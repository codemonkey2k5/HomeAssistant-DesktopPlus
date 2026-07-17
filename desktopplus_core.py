"""
DesktopPlus — desktop dashboard panel for Windows (Home Assistant friendly, any URL).

Version 2.1.1: reliability hardening for long unattended runs.
Feature set unchanged from 2.0.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
LOG_PATH = BASE_DIR / "desktopplus.log"
LOG_BACKUP_PATH = BASE_DIR / "desktopplus.log.1"
ICON_PATH = BASE_DIR / "tray_icon.png"

DEFAULT_URL = ""
APP_NAME = "DesktopPlus"
__version__ = "2.1.1"

# Max log size before rotation (one backup kept).
LOG_MAX_BYTES = 2 * 1024 * 1024

# Outward overscan for mixed-DPI hairlines (unchanged from 2.0).
EDGE_OVERSCAN_PX = 2

REFRESH_INTERVAL_CHOICES = (300, 600, 900, 1800, 3600)

# ---------------------------------------------------------------------------
# Logging (rotated — safe for months-long runs)
# ---------------------------------------------------------------------------

def log(message: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {message}"
    try:
        if LOG_PATH.exists() and LOG_PATH.stat().st_size >= LOG_MAX_BYTES:
            try:
                if LOG_BACKUP_PATH.exists():
                    LOG_BACKUP_PATH.unlink()
                LOG_PATH.replace(LOG_BACKUP_PATH)
            except Exception:
                pass
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line)
    except Exception:
        pass


def show_error(message: str, title: str = f"{APP_NAME} — Error") -> None:
    log(f"ERROR: {message}")
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


def show_info(message: str, title: str = APP_NAME) -> None:
    log(f"INFO: {message}")
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
            return
        except Exception:
            pass
    print(message)


# ---------------------------------------------------------------------------
# DPI awareness (Windows) — before geometry queries
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    except Exception:
        pass


try:
    import webview
    from PIL import Image, ImageDraw  # noqa: F401 — used by UI module import chain
    from pystray import Icon, Menu, MenuItem  # noqa: F401
except ImportError as exc:
    show_error(
        "Missing Python package required to run this app.\n\n"
        f"Detail: {exc}\n\n"
        f"This file was opened with:\n{sys.executable}\n"
        f"Python {sys.version.split()[0]}\n\n"
        "Fix (run in a terminal):\n"
        f'  "{sys.executable}" -m pip install pywebview pystray pillow\n\n'
        "Or install for every Python you have, then double-click again.\n"
        f"A log is written to:\n{LOG_PATH}"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class AppConfig:
    url: str = DEFAULT_URL
    display_index: int = 0
    fit_work_area: bool = True
    refresh_enabled: bool = True
    refresh_interval_seconds: int = 600
    scrolling_enabled: bool = False
    show_scrollbars: bool = False
    frameless: bool = True
    resizable: bool = False
    on_top: bool = False
    allow_move: bool = False
    private_mode: bool = False
    window_title: str = APP_NAME

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        known = {f.name for f in fields(cls)}
        cleaned = {k: v for k, v in data.items() if k in known}
        cfg = cls(**cleaned)
        if cfg.refresh_interval_seconds < 30:
            cfg.refresh_interval_seconds = 30
        if cfg.display_index < 0:
            cfg.display_index = 0
        if isinstance(cfg.url, str):
            cfg.url = cfg.url.strip()
        else:
            cfg.url = DEFAULT_URL
        return cfg


def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        cfg = AppConfig()
        mons = get_monitors()
        cfg.display_index = _default_display_index(mons)
        save_config(cfg)
        return cfg
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("config root must be an object")
        return AppConfig.from_dict(data)
    except Exception as e:
        log(f"config load failed: {e}; recreating defaults")
        cfg = AppConfig()
        save_config(cfg)
        return cfg


def save_config(cfg: AppConfig) -> None:
    """Atomic write so a crash mid-save cannot wipe an existing config (keeps URL on upgrade)."""
    try:
        tmp_path = CONFIG_PATH.with_suffix(".json.tmp")
        data = json.dumps(asdict(cfg), indent=2)
        with tmp_path.open("w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
        tmp_path.replace(CONFIG_PATH)
    except Exception as e:
        log(f"config save failed: {e}")
        try:
            tmp_path = CONFIG_PATH.with_suffix(".json.tmp")
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Monitors / work area
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MonitorInfo:
    index: int
    name: str
    is_primary: bool
    mon_x: int
    mon_y: int
    mon_w: int
    mon_h: int
    work_x: int
    work_y: int
    work_w: int
    work_h: int

    @property
    def has_taskbar_inset(self) -> bool:
        return (self.work_w, self.work_h) != (self.mon_w, self.mon_h)

    def label(self) -> str:
        role = "Primary" if self.is_primary else "Display"
        tb = " · taskbar" if self.has_taskbar_inset else ""
        return (
            f"{self.index + 1}: {role} {self.mon_w}x{self.mon_h}"
            f" (work {self.work_w}x{self.work_h}){tb}"
        )

    def geometry(self, fit_work_area: bool) -> Tuple[int, int, int, int]:
        if fit_work_area:
            return self.work_x, self.work_y, self.work_w, self.work_h
        return self.mon_x, self.mon_y, self.mon_w, self.mon_h


def get_monitors() -> List[MonitorInfo]:
    """Enumerate all displays via Windows APIs (any count/size/arrangement)."""
    if sys.platform != "win32":
        result: List[MonitorInfo] = []
        for i, s in enumerate(webview.screens):
            result.append(
                MonitorInfo(
                    index=i,
                    name=f"Screen {i + 1}",
                    is_primary=(i == 0),
                    mon_x=int(s.x),
                    mon_y=int(s.y),
                    mon_w=int(s.width),
                    mon_h=int(s.height),
                    work_x=int(s.x),
                    work_y=int(s.y),
                    work_w=int(s.width),
                    work_h=int(s.height),
                )
            )
        return result

    import ctypes
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
            ("szDevice", wintypes.WCHAR * 32),
        ]

    MONITORINFOF_PRIMARY = 0x00000001
    raw: List[dict] = []

    def _enum_proc(h_monitor, _hdc, _lprc, _data):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if ctypes.windll.user32.GetMonitorInfoW(h_monitor, ctypes.byref(info)):
            m = info.rcMonitor
            w = info.rcWork
            raw.append(
                {
                    "name": info.szDevice,
                    "is_primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                    "mon": (m.left, m.top, m.right - m.left, m.bottom - m.top),
                    "work": (w.left, w.top, w.right - w.left, w.bottom - w.top),
                }
            )
        return 1

    MonitorEnumProc = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
    )
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_enum_proc), 0)

    raw.sort(key=lambda d: (not d["is_primary"], d["mon"][0], d["mon"][1]))

    monitors: List[MonitorInfo] = []
    for i, d in enumerate(raw):
        mx, my, mw, mh = d["mon"]
        wx, wy, ww, wh = d["work"]
        monitors.append(
            MonitorInfo(
                index=i,
                name=d["name"],
                is_primary=d["is_primary"],
                mon_x=mx,
                mon_y=my,
                mon_w=mw,
                mon_h=mh,
                work_x=wx,
                work_y=wy,
                work_w=ww,
                work_h=wh,
            )
        )
    return monitors


def _default_display_index(mons: Sequence[MonitorInfo]) -> int:
    if not mons:
        return 0
    for m in mons:
        if not m.is_primary:
            return m.index
    return 0


def clamp_display_index(index: int, mons: Sequence[MonitorInfo]) -> int:
    if not mons:
        return 0
    return max(0, min(int(index), len(mons) - 1))


def resolve_geometry(cfg: AppConfig) -> Tuple[int, int, int, int, MonitorInfo]:
    mons = get_monitors()
    if not mons:
        dummy = MonitorInfo(0, "fallback", True, 0, 0, 1280, 720, 0, 0, 1280, 720)
        return 0, 0, 1280, 720, dummy
    idx = clamp_display_index(cfg.display_index, mons)
    mon = mons[idx]
    x, y, w, h = mon.geometry(cfg.fit_work_area)
    if w < 100 or h < 100:
        x, y, w, h = mon.geometry(False)
    return x, y, w, h, mon


def primary_scale_factor() -> float:
    """Primary monitor scale (pywebview multiplies create_window x/y by this on Windows)."""
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes

        return float(ctypes.windll.shcore.GetScaleFactorForDevice(0)) / 100.0
    except Exception:
        return 1.0


def pywebview_create_xy(x: int, y: int) -> Tuple[int, int]:
    """Pre-divide coords so pywebview's primary-DPI multiply lands correctly."""
    sf = primary_scale_factor()
    if sf <= 0:
        sf = 1.0
    return int(round(x / sf)), int(round(y / sf))


def _window_hwnd(window: Any) -> Optional[int]:
    native = getattr(window, "native", None)
    if native is None:
        return None
    try:
        handle = native.Handle
        if hasattr(handle, "ToInt32"):
            return int(handle.ToInt32())
        return int(handle)
    except Exception:
        return None


def apply_window_chrome_tweaks(window: Any) -> None:
    """Remove rounded corners / DWM border insets on frameless panel windows."""
    if sys.platform != "win32":
        return
    import ctypes

    hwnd = _window_hwnd(window)
    native = getattr(window, "native", None)

    if native is not None:
        try:
            from System.Windows.Forms import Padding  # type: ignore

            native.Padding = Padding(0)
        except Exception:
            pass
        try:
            native.AutoScaleMode = 0  # None
        except Exception:
            pass

    if not hwnd:
        return

    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWCP_DONOTROUND = 1
    DWMWA_BORDER_COLOR = 34
    DWMWA_COLOR_NONE = 0xFFFFFFFE
    DWMWA_NCRENDERING_POLICY = 2
    DWMNCRP_DISABLED = 1

    def _set_dwm_int(attr: int, value: int) -> None:
        val = ctypes.c_int(value)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)
        )

    try:
        _set_dwm_int(DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_DONOTROUND)
    except Exception as e:
        log(f"DWM corner tweak failed: {e}")
    try:
        _set_dwm_int(DWMWA_BORDER_COLOR, DWMWA_COLOR_NONE)
    except Exception as e:
        log(f"DWM border tweak failed: {e}")
    try:
        _set_dwm_int(DWMWA_NCRENDERING_POLICY, DWMNCRP_DISABLED)
    except Exception:
        pass


def set_native_bounds(
    window: Any,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    activate: bool = False,
) -> bool:
    """
    Place the window using real virtual-screen pixels (Win32 SetWindowPos).

    activate=False (default): do not BringToFront / force refresh — critical for a
    desktop-background style panel and for reducing GPU/focus thrash after refresh.
    """
    x, y, w, h = int(x), int(y), int(w), int(h)

    pad = max(0, int(EDGE_OVERSCAN_PX))
    if pad:
        x -= pad
        y -= pad
        w += pad * 2
        h += pad * 2

    if w < 100:
        w = 100
    if h < 100:
        h = 100

    if sys.platform != "win32":
        try:
            window.resize(w, h)
            window.move(x, y)
            return True
        except Exception as e:
            log(f"set_native_bounds fallback failed: {e}")
            return False

    import ctypes

    hwnd = _window_hwnd(window)
    native = getattr(window, "native", None)

    SWP_NOZORDER = 0x0004
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040
    SWP_FRAMECHANGED = 0x0020
    SWP_NOCOPYBITS = 0x0100

    flags = SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOCOPYBITS
    if activate:
        flags |= SWP_SHOWWINDOW
    else:
        # Place without activating / stealing focus
        flags |= SWP_NOACTIVATE | SWP_SHOWWINDOW

    def _apply() -> None:
        apply_window_chrome_tweaks(window)

        if native is not None:
            try:
                if int(native.WindowState) != 0:
                    native.WindowState = 0
            except Exception:
                pass

        if hwnd:
            try:
                ctypes.windll.kernel32.SetLastError(0)
            except Exception:
                pass
            ok = ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, w, h, flags)
            if not ok:
                try:
                    err = ctypes.get_last_error()
                except Exception:
                    err = "?"
                log(f"SetWindowPos failed last_error={err} hwnd={hwnd} {x},{y} {w}x{h}")
            else:
                log(f"SetWindowPos ok hwnd={hwnd} {x},{y} {w}x{h} activate={activate}")

            try:
                if native is not None and native.Controls.Count > 0:
                    for ctrl in native.Controls:
                        try:
                            ctrl.Left = 0
                            ctrl.Top = 0
                            ctrl.Width = native.ClientSize.Width
                            ctrl.Height = native.ClientSize.Height
                            ctrl.Dock = 5  # Fill
                        except Exception:
                            pass
            except Exception as e:
                log(f"child fill tweak failed: {e}")

        if native is not None and activate:
            try:
                native.Show()
                native.BringToFront()
            except Exception:
                pass

    try:
        if native is not None and getattr(native, "InvokeRequired", False):
            from System import Action  # type: ignore

            native.Invoke(Action(_apply))
        else:
            _apply()
        return True
    except Exception as e:
        log(f"set_native_bounds invoke path failed: {e}; trying direct")
        try:
            _apply()
            return True
        except Exception as e2:
            log(f"set_native_bounds failed: {e2}")
            try:
                sf = primary_scale_factor() or 1.0
                window.resize(w, h)
                window.move(int(round(x / sf)), int(round(y / sf)))
                return True
            except Exception as e3:
                log(f"set_native_bounds ultimate fallback failed: {e3}")
                return False


# ---------------------------------------------------------------------------
# URL dialog
# ---------------------------------------------------------------------------

def prompt_for_url(current: str, title: str = "Dashboard URL") -> Optional[str]:
    """Show a small dialog to enter/change the start URL. Returns None if cancelled."""
    try:
        import tkinter as tk
        from tkinter import simpledialog
    except Exception as e:
        log(f"tkinter unavailable: {e}")
        return None

    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    root.update_idletasks()
    try:
        result = simpledialog.askstring(
            title,
            "URL to open on start (and when refreshing):\n"
            "Example: http://homeassistant.local:8123/lovelace/0",
            initialvalue=current or "",
            parent=root,
        )
    finally:
        try:
            root.destroy()
        except Exception:
            pass
    if result is None:
        return None
    return result.strip()


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if "://" not in url:
        url = "http://" + url
    return url


# ---------------------------------------------------------------------------
# Scroll / page alignment helpers
# ---------------------------------------------------------------------------

def build_scroll_css(cfg: AppConfig) -> str:
    parts: List[str] = []
    if not cfg.show_scrollbars:
        parts.append(
            """
            * { scrollbar-width: none !important; }
            *::-webkit-scrollbar { width: 0 !important; height: 0 !important; display: none !important; }
            """
        )
    if not cfg.scrolling_enabled:
        parts.append(
            """
            html, body {
                overflow: hidden !important;
                overscroll-behavior: none !important;
            }
            """
        )
    return "\n".join(parts)


def build_scroll_js(cfg: AppConfig) -> str:
    scroll_on = "true" if cfg.scrolling_enabled else "false"
    bars_on = "true" if cfg.show_scrollbars else "false"
    return f"""
    (function() {{
        const SCROLLING = {scroll_on};
        const BARS = {bars_on};
        const FLAG = '__desktopplus_scroll_policy';
        if (!window[FLAG]) {{
            window[FLAG] = {{ allowScroll: true }};
            window[FLAG].wheel = function(e) {{
                if (!window[FLAG].allowScroll) {{ e.preventDefault(); }}
            }};
            window.addEventListener('wheel', window[FLAG].wheel, {{ passive: false, capture: true }});
        }}
        window[FLAG].allowScroll = SCROLLING;
        let style = document.getElementById('desktopplus-scroll-style');
        if (!style) {{
            style = document.createElement('style');
            style.id = 'desktopplus-scroll-style';
            (document.head || document.documentElement).appendChild(style);
        }}
        let css = '';
        if (!BARS) {{
            css += '*{{scrollbar-width:none!important;}}';
            css += '*::-webkit-scrollbar{{width:0!important;height:0!important;display:none!important;}}';
        }}
        if (!SCROLLING) {{
            css += 'html,body{{overflow:hidden!important;overscroll-behavior:none!important;}}';
        }}
        style.textContent = css;
    }})();
    """


def build_reset_scroll_js() -> str:
    """
    Force page content to top-left after reload.
    Bounded work only — no MutationObservers, no deep infinite walks.
    """
    return """
    (function() {
        try {
            window.scrollTo(0, 0);
            if (document.documentElement) {
                document.documentElement.scrollTop = 0;
                document.documentElement.scrollLeft = 0;
            }
            if (document.body) {
                document.body.scrollTop = 0;
                document.body.scrollLeft = 0;
            }
            // Best-effort: a few common scroll containers (Home Assistant panels)
            var sel = 'ha-app-layout, #view, [scroller], .scroll, main, ion-content';
            var nodes = document.querySelectorAll(sel);
            var n = Math.min(nodes.length, 40);
            for (var i = 0; i < n; i++) {
                try {
                    nodes[i].scrollTop = 0;
                    nodes[i].scrollLeft = 0;
                } catch (e) {}
            }
        } catch (e) {}
    })();
    """


def reset_page_scroll(window: Any) -> None:
    """Reset document scroll after navigation/refresh."""
    if window is None:
        return
    try:
        window.evaluate_js(build_reset_scroll_js())
    except Exception as e:
        log(f"reset_page_scroll failed: {e}")
