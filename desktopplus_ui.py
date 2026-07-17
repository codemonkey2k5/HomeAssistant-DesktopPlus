"""
DesktopPlus UI, tray, and entrypoint.

Version 2.1.1: all webview/Win32 work runs on the backend loop thread via a command
queue so the tray never blocks and refresh is reliable.
"""

from __future__ import annotations

import queue
import sys
import threading
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import webview
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from desktopplus_core import (
    APP_NAME,
    BASE_DIR,
    CONFIG_PATH,
    ICON_PATH,
    REFRESH_INTERVAL_CHOICES,
    AppConfig,
    apply_window_chrome_tweaks,
    build_scroll_css,
    build_scroll_js,
    clamp_display_index,
    get_monitors,
    load_config,
    log,
    normalize_url,
    primary_scale_factor,
    prompt_for_url,
    pywebview_create_xy,
    reset_page_scroll,
    resolve_geometry,
    set_native_bounds,
    show_error,
    save_config,
    __version__,
)


# ---------------------------------------------------------------------------
# Tray icon image
# ---------------------------------------------------------------------------

def make_tray_image(size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 1
    draw.rounded_rectangle(
        (margin, margin, size - 1 - margin, size - 1 - margin),
        radius=size // 5,
        fill=(18, 28, 40, 255),
    )

    bezel = (0, 188, 212, 255)
    mx0, my0 = size * 0.14, size * 0.16
    mx1, my1 = size * 0.86, size * 0.68
    draw.rounded_rectangle((mx0, my0, mx1, my1), radius=size // 12, fill=bezel)

    inset = size * 0.06
    sx0, sy0 = mx0 + inset, my0 + inset
    sx1, sy1 = mx1 - inset, my1 - inset
    draw.rounded_rectangle((sx0, sy0, sx1, sy1), radius=size // 18, fill=(12, 18, 28, 255))

    gap = size * 0.04
    tile_w = (sx1 - sx0 - gap * 3) / 2
    tile_h = (sy1 - sy0 - gap * 3) / 2
    colors = [
        (3, 169, 244, 255),
        (0, 200, 150, 255),
        (255, 171, 64, 255),
        (171, 71, 188, 255),
    ]
    coords = [
        (sx0 + gap, sy0 + gap),
        (sx0 + gap * 2 + tile_w, sy0 + gap),
        (sx0 + gap, sy0 + gap * 2 + tile_h),
        (sx0 + gap * 2 + tile_w, sy0 + gap * 2 + tile_h),
    ]
    for (tx, ty), color in zip(coords, colors):
        draw.rounded_rectangle(
            (tx, ty, tx + tile_w, ty + tile_h),
            radius=max(2, size // 20),
            fill=color,
        )

    stand_w = size * 0.18
    stand_h = size * 0.08
    cx = size / 2
    stand_top = my1
    draw.rectangle(
        (cx - stand_w * 0.2, stand_top, cx + stand_w * 0.2, stand_top + stand_h),
        fill=bezel,
    )
    draw.rounded_rectangle(
        (
            cx - stand_w,
            stand_top + stand_h * 0.65,
            cx + stand_w,
            stand_top + stand_h + size * 0.06,
        ),
        radius=2,
        fill=bezel,
    )
    return img


def get_tray_image() -> Image.Image:
    try:
        if ICON_PATH.exists():
            with Image.open(ICON_PATH) as im:
                return im.convert("RGBA")
    except Exception as e:
        log(f"could not load tray_icon.png: {e}")
    img = make_tray_image(64)
    try:
        img.save(ICON_PATH)
        make_tray_image(256).save(BASE_DIR / "tray_icon_256.png")
    except Exception as e:
        log(f"could not save tray icon: {e}")
    return img


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class App:
    def __init__(self) -> None:
        self.cfg = load_config()
        self.window: Optional[Any] = None
        self.icon: Optional[Icon] = None
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._refresh_deadline = 0.0
        self.page_title: str = ""
        self._last_tray_label: str = ""
        # Commands processed only on the webview backend thread
        self._cmds: queue.Queue = queue.Queue()
        # Deferred work: list of (run_at_monotonic, name, kwargs)
        self._deferred: List[Tuple[float, str, Dict[str, Any]]] = []
        self._deferred_lock = threading.Lock()

    # --- config ------------------------------------------------------------

    def update_config(self, **kwargs: Any) -> AppConfig:
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.cfg, key):
                    setattr(self.cfg, key, value)
            if "url" in kwargs and isinstance(self.cfg.url, str):
                self.cfg.url = normalize_url(self.cfg.url)
            save_config(self.cfg)
            cfg = AppConfig.from_dict(asdict(self.cfg))
        if "display_index" in kwargs or "url" in kwargs:
            self.enqueue("update_title")
        return cfg

    def get_config(self) -> AppConfig:
        with self._lock:
            return AppConfig.from_dict(asdict(self.cfg))

    # --- command queue ----------------------------------------------------

    def enqueue(self, name: str, **kwargs: Any) -> None:
        """Thread-safe: tray / timers only enqueue; backend_loop executes."""
        try:
            self._cmds.put_nowait((name, kwargs))
        except Exception as e:
            log(f"enqueue failed {name}: {e}")

    def enqueue_after(self, delay_s: float, name: str, **kwargs: Any) -> None:
        run_at = time.monotonic() + max(0.0, delay_s)
        with self._deferred_lock:
            self._deferred.append((run_at, name, kwargs))

    def _drain_deferred(self) -> None:
        now = time.monotonic()
        due: List[Tuple[str, Dict[str, Any]]] = []
        with self._deferred_lock:
            keep: List[Tuple[float, str, Dict[str, Any]]] = []
            for run_at, name, kwargs in self._deferred:
                if run_at <= now:
                    due.append((name, kwargs))
                else:
                    keep.append((run_at, name, kwargs))
            self._deferred = keep
        for name, kwargs in due:
            self._dispatch(name, kwargs)

    def _dispatch(self, name: str, kwargs: Dict[str, Any]) -> None:
        try:
            if name == "refresh":
                self._do_refresh()
            elif name == "geometry":
                self._do_geometry()
            elif name == "scroll":
                self._do_scroll_policy()
            elif name == "on_top":
                self._do_on_top()
            elif name == "set_url":
                url = kwargs.get("url") or ""
                self._do_set_url(url)
            elif name == "update_title":
                self._do_refresh_page_title()
            elif name == "post_load":
                self._do_post_load()
            elif name == "chrome":
                if self.window is not None:
                    apply_window_chrome_tweaks(self.window)
            else:
                log(f"unknown command: {name}")
        except Exception as e:
            log(f"command {name} failed: {e}\n{traceback.format_exc()}")

    def _process_cmds(self) -> None:
        while True:
            try:
                name, kwargs = self._cmds.get_nowait()
            except queue.Empty:
                break
            self._dispatch(name, kwargs)

    # --- identity / tray label --------------------------------------------

    def screen_number(self) -> int:
        cfg = self.get_config()
        mons = get_monitors()
        idx = clamp_display_index(cfg.display_index, mons)
        return idx + 1

    def tray_label(self) -> str:
        screen = self.screen_number()
        title = (self.page_title or "").strip()
        if title.lower() == "about:blank":
            title = ""
        if len(title) > 40:
            title = title[:37] + "..."
        if title:
            return f"{APP_NAME} | Screen {screen} | {title}"
        return f"{APP_NAME} | Screen {screen}"

    def update_tray_title(self) -> None:
        label = self.tray_label()
        icon = self.icon
        if icon is not None:
            try:
                icon.title = label
            except Exception as e:
                log(f"tray title update failed: {e}")
        if label != self._last_tray_label:
            self._last_tray_label = label
            log(f"tray label: {label}")

    def _do_refresh_page_title(self) -> None:
        window = self.window
        if window is None:
            self.update_tray_title()
            return
        title = ""
        try:
            result = window.evaluate_js(
                "(function(){ try { return document.title || ''; } catch(e) { return ''; } })()"
            )
            if result is not None:
                title = str(result).strip()
        except Exception as e:
            log(f"page title read failed: {e}")
        self.page_title = title
        self.update_tray_title()
        try:
            window.set_title(self.tray_label())
        except Exception:
            pass

    # --- webview ops (backend thread only) --------------------------------

    def _do_geometry(self) -> None:
        window = self.window
        if window is None:
            return
        cfg = self.get_config()
        mons = get_monitors()
        idx = clamp_display_index(cfg.display_index, mons)
        if idx != cfg.display_index:
            self.update_config(display_index=idx)
            cfg = self.get_config()
        x, y, w, h, mon = resolve_geometry(cfg)
        log(
            f"geometry -> display {mon.index + 1} ({mon.name}): "
            f"x={x} y={y} {w}x{h} fit_work_area={cfg.fit_work_area}"
        )
        ok = set_native_bounds(window, x, y, w, h, activate=False)
        if not ok:
            self._notify("Could not move window to the selected display.")
        self.update_tray_title()

    def _do_scroll_policy(self) -> None:
        window = self.window
        if window is None:
            return
        cfg = self.get_config()
        css = build_scroll_css(cfg)
        try:
            if css.strip():
                window.load_css(css)
        except Exception:
            pass
        try:
            window.evaluate_js(build_scroll_js(cfg))
        except Exception:
            pass

    def _do_on_top(self) -> None:
        window = self.window
        if window is None:
            return
        cfg = self.get_config()
        try:
            window.on_top = cfg.on_top
        except Exception as e:
            log(f"on_top failed: {e}")

    def _do_set_url(self, url: str) -> None:
        url = normalize_url(url)
        if not url:
            return
        self.update_config(url=url)
        window = self.window
        if window is not None:
            try:
                window.load_url(url)
                self._arm_refresh_deadline()
                log(f"loaded url: {url}")
            except Exception as e:
                self._notify(f"Could not load URL: {e}")
                log(f"load_url failed: {e}")

    def _do_refresh(self) -> None:
        """Hard reload on the correct thread. No URL rewriting."""
        window = self.window
        if window is None:
            self._arm_refresh_deadline()
            return
        cfg = self.get_config()
        if not cfg.url:
            self._notify("No URL set. Use Set dashboard URL…")
            self._arm_refresh_deadline()
            return
        try:
            window.evaluate_js("location.reload()")
            log("refreshed via location.reload()")
        except Exception as e1:
            log(f"location.reload failed: {e1}; trying load_url")
            try:
                window.load_url(cfg.url)
                log("refreshed via load_url")
            except Exception as e2:
                self._notify(f"Refresh failed: {e2}")
                log(f"refresh failed: {e2}")
        # Always re-arm so a failed refresh cannot stall auto-refresh for a day
        self._arm_refresh_deadline()

    def _do_post_load(self) -> None:
        """After DOM ready: scroll top, policy, quiet geometry, title."""
        self._do_scroll_policy()
        reset_page_scroll(self.window)
        self._do_geometry()
        self._do_refresh_page_title()
        # HA often sets document.title late
        self.enqueue_after(1.0, "update_title")

    def _arm_refresh_deadline(self) -> None:
        cfg = self.get_config()
        if cfg.refresh_enabled and cfg.refresh_interval_seconds > 0:
            self._refresh_deadline = time.monotonic() + cfg.refresh_interval_seconds
        else:
            self._refresh_deadline = 0.0

    def _notify(self, message: str) -> None:
        log(f"notify: {message}")
        icon = self.icon
        if icon is None:
            return
        try:
            icon.notify(message, APP_NAME)
        except Exception:
            pass

    # --- backend loop -----------------------------------------------------

    def backend_loop(self, window: Any) -> None:
        self.window = window
        log(f"backend_loop started (v{__version__})")

        def on_loaded() -> None:
            # Keep this handler short — defer work to the queue
            self.enqueue("post_load")

        try:
            window.events.loaded += on_loaded
        except Exception as e:
            log(f"events.loaded subscribe failed: {e}")

        # First paint: chrome + on_top; full layout/scroll/title come from post_load
        # when the page fires "loaded" (avoids doing the same work twice at startup).
        self.enqueue("chrome")
        self.enqueue("on_top")
        self._arm_refresh_deadline()

        while not self._stop.is_set():
            try:
                if not webview.windows:
                    break
            except Exception:
                break

            self._process_cmds()
            self._drain_deferred()

            cfg = self.get_config()
            if (
                cfg.refresh_enabled
                and cfg.refresh_interval_seconds > 0
                and self._refresh_deadline > 0
                and time.monotonic() >= self._refresh_deadline
            ):
                # Prevent re-queue until _do_refresh re-arms the real deadline
                self._refresh_deadline = time.monotonic() + 86400.0
                self.enqueue("refresh")

            # Idle wait: slightly longer when quiet → less CPU
            time.sleep(0.5 if not self._cmds.empty() else 0.75)

        log("backend_loop ending")
        self._stop.set()
        self._stop_tray()

    def _stop_tray(self) -> None:
        icon = self.icon
        if icon is not None:
            try:
                icon.stop()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# System tray (handlers must not call webview APIs)
# ---------------------------------------------------------------------------

def build_tray_menu(app: App) -> Menu:
    def cfg() -> AppConfig:
        return app.get_config()

    def rebuild_menu(icon: Icon) -> None:
        try:
            icon.menu = build_tray_menu(app)
            icon.update_menu()
        except Exception as e:
            log(f"tray menu rebuild failed: {e}")

    def set_and(**kwargs: Any) -> Callable:
        def handler(icon: Icon, _item: MenuItem) -> None:
            app.update_config(**kwargs)
            if "on_top" in kwargs:
                app.enqueue("on_top")
            if "fit_work_area" in kwargs or "display_index" in kwargs:
                app.enqueue("geometry")
            if "scrolling_enabled" in kwargs or "show_scrollbars" in kwargs:
                app.enqueue("scroll")
            if "refresh_enabled" in kwargs or "refresh_interval_seconds" in kwargs:
                # Arm on backend via a no-op refresh deadline update
                app.enqueue("update_title")  # cheap; deadline armed below
                # Arm deadline immediately (config only, no webview)
                cfg_now = app.get_config()
                if cfg_now.refresh_enabled and cfg_now.refresh_interval_seconds > 0:
                    app._refresh_deadline = (
                        time.monotonic() + cfg_now.refresh_interval_seconds
                    )
                else:
                    app._refresh_deadline = 0.0
            if "frameless" in kwargs or "resizable" in kwargs or "allow_move" in kwargs:
                app._notify("Saved. Restart the app to apply this window option.")
            rebuild_menu(icon)

        return handler

    def toggle(field: str) -> Callable:
        def handler(icon: Icon, item: MenuItem) -> None:
            current = getattr(cfg(), field)
            set_and(**{field: not current})(icon, item)

        return handler

    def checked(field: str) -> Callable[[MenuItem], bool]:
        return lambda _item: bool(getattr(cfg(), field))

    def display_items() -> Tuple[MenuItem, ...]:
        mons = get_monitors()
        if not mons:
            return (MenuItem("No monitors found", None, enabled=False),)
        items: List[MenuItem] = []
        for m in mons:
            items.append(
                MenuItem(
                    m.label(),
                    set_and(display_index=m.index),
                    checked=lambda _item, i=m.index: clamp_display_index(
                        cfg().display_index, get_monitors()
                    )
                    == i,
                    radio=True,
                )
            )
        return tuple(items)

    def interval_items() -> Tuple[MenuItem, ...]:
        labels = {
            300: "5 minutes",
            600: "10 minutes",
            900: "15 minutes",
            1800: "30 minutes",
            3600: "60 minutes",
        }
        items: List[MenuItem] = []
        for seconds in REFRESH_INTERVAL_CHOICES:
            items.append(
                MenuItem(
                    labels.get(seconds, f"{seconds}s"),
                    set_and(refresh_interval_seconds=seconds),
                    checked=lambda _item, s=seconds: cfg().refresh_interval_seconds == s,
                    radio=True,
                )
            )
        return tuple(items)

    def on_set_url(icon: Icon, _item: MenuItem) -> None:
        current = cfg().url

        def worker() -> None:
            new_url = prompt_for_url(current)
            if new_url is None:
                return
            new_url = normalize_url(new_url)
            if not new_url:
                app._notify("URL was empty; not changed.")
                return
            app.enqueue("set_url", url=new_url)
            app._notify("URL updated")
            rebuild_menu(icon)

        threading.Thread(target=worker, daemon=True).start()

    def on_refresh_now(_icon: Icon, _item: MenuItem) -> None:
        app.enqueue("refresh")

    def on_reapply_layout(_icon: Icon, _item: MenuItem) -> None:
        app.enqueue("geometry")
        app.enqueue("scroll")
        app._notify("Layout re-applied")

    def on_show_url(_icon: Icon, _item: MenuItem) -> None:
        u = cfg().url or "(not set)"
        app._notify(u if len(u) < 120 else u[:117] + "...")

    def on_open_config_folder(_icon: Icon, _item: MenuItem) -> None:
        try:
            if sys.platform == "win32":
                import os

                os.startfile(str(BASE_DIR))  # noqa: S606
        except Exception as e:
            log(f"open folder failed: {e}")

    def on_quit(icon: Icon, _item: MenuItem) -> None:
        app._stop.set()
        try:
            for w in list(webview.windows):
                w.destroy()
        except Exception:
            pass
        try:
            icon.stop()
        except Exception:
            pass

    url_preview = cfg().url or "(not set)"
    if len(url_preview) > 42:
        url_preview = url_preview[:39] + "..."

    return Menu(
        MenuItem("Refresh now", on_refresh_now),
        MenuItem("Re-apply layout", on_reapply_layout),
        Menu.SEPARATOR,
        MenuItem("Set dashboard URL…", on_set_url),
        MenuItem(f"URL: {url_preview}", on_show_url),
        Menu.SEPARATOR,
        MenuItem(
            "Auto-refresh",
            toggle("refresh_enabled"),
            checked=checked("refresh_enabled"),
        ),
        MenuItem("Refresh interval", Menu(lambda: interval_items())),
        Menu.SEPARATOR,
        MenuItem("Display", Menu(lambda: display_items())),
        MenuItem(
            "Fit work area (normal mode)",
            toggle("fit_work_area"),
            checked=checked("fit_work_area"),
        ),
        MenuItem("  Off = kiosk (full monitor)", None, enabled=False),
        Menu.SEPARATOR,
        MenuItem(
            "Scrolling enabled",
            toggle("scrolling_enabled"),
            checked=checked("scrolling_enabled"),
        ),
        MenuItem(
            "Show scrollbars",
            toggle("show_scrollbars"),
            checked=checked("show_scrollbars"),
        ),
        Menu.SEPARATOR,
        MenuItem(
            "Frameless (restart)",
            toggle("frameless"),
            checked=checked("frameless"),
        ),
        MenuItem(
            "Resizable (restart)",
            toggle("resizable"),
            checked=checked("resizable"),
        ),
        MenuItem(
            "Allow move / drag (restart)",
            toggle("allow_move"),
            checked=checked("allow_move"),
        ),
        MenuItem(
            "Always on top",
            toggle("on_top"),
            checked=checked("on_top"),
        ),
        Menu.SEPARATOR,
        MenuItem("Open config folder", on_open_config_folder),
        MenuItem("Quit", on_quit),
    )


def start_tray(app: App) -> None:
    try:
        menu = build_tray_menu(app)
        icon_name = f"DesktopPlus-S{app.screen_number()}"
        icon = Icon(icon_name, get_tray_image(), app.tray_label(), menu)
        app.icon = icon
        log(f"tray icon starting ({app.tray_label()})")
        icon.run()
    except Exception as e:
        log(f"tray failed: {e}\n{traceback.format_exc()}")
        show_error(f"System tray failed to start:\n{e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    log(f"=== {APP_NAME} v{__version__} starting ===")
    log(f"python={sys.executable}")
    log(f"version={sys.version}")
    log(f"script={Path(__file__).resolve()}")

    try:
        get_tray_image()
    except Exception as e:
        log(f"icon init: {e}")

    app = App()
    cfg = app.get_config()

    mons = get_monitors()
    log(f"monitors found: {len(mons)}")
    for m in mons:
        log(f"  {m.label()} device={m.name}")

    if mons:
        idx = clamp_display_index(cfg.display_index, mons)
        if idx != cfg.display_index:
            cfg = app.update_config(display_index=idx)

    if not cfg.url:
        log("no URL configured; prompting")
        entered = prompt_for_url(
            "",
            title=f"{APP_NAME} — Set start URL",
        )
        if entered is None or not entered.strip():
            show_error(
                "A start URL is required.\n\n"
                "Run the app again and enter your dashboard URL,\n"
                "or edit config.json next to the script.\n\n"
                f"Config path:\n{CONFIG_PATH}"
            )
            return 1
        cfg = app.update_config(url=normalize_url(entered))

    x, y, w, h, mon = resolve_geometry(cfg)
    create_x, create_y = pywebview_create_xy(x, y)
    log(
        f"initial geometry on {mon.label()}: real=({x},{y}) {w}x{h} "
        f"create_xy=({create_x},{create_y}) scale={primary_scale_factor()}"
    )

    easy_drag = bool(cfg.frameless and cfg.allow_move)
    start_url = cfg.url

    try:
        initial_title = (
            f"{APP_NAME} | Screen {clamp_display_index(cfg.display_index, mons) + 1}"
        )
        window = webview.create_window(
            initial_title,
            start_url,
            x=create_x,
            y=create_y,
            width=w,
            height=h,
            frameless=cfg.frameless,
            resizable=cfg.resizable,
            on_top=cfg.on_top,
            easy_drag=easy_drag,
            shadow=False,
            background_color="#000000",
        )
    except Exception as e:
        show_error(f"Could not create window:\n{e}")
        return 1

    app.window = window

    def _on_shown() -> None:
        apply_window_chrome_tweaks(window)
        app.enqueue("geometry")

    try:
        window.events.shown += _on_shown
    except Exception as e:
        log(f"events.shown subscribe failed: {e}")

    tray_thread = threading.Thread(target=start_tray, args=(app,), daemon=True)
    tray_thread.start()

    try:
        webview.start(app.backend_loop, window, private_mode=cfg.private_mode)
    except Exception as e:
        app._stop.set()
        app._stop_tray()
        show_error(
            f"Failed to start the web view:\n{e}\n\n"
            "On Windows this usually needs the free Microsoft Edge WebView2 Runtime.\n"
            "https://developer.microsoft.com/microsoft-edge/webview2/"
        )
        return 1
    finally:
        app._stop.set()
        app._stop_tray()
        log("=== shutdown ===")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        tb = traceback.format_exc()
        log(tb)
        show_error(f"Unexpected error:\n{tb[-1500:]}")
        sys.exit(1)
