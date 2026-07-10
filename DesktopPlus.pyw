"""DesktopPlus — double-click to run."""
from desktopplus_ui import main
import sys

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback
        from desktopplus_core import log, show_error
        tb = traceback.format_exc()
        log(tb)
        show_error(f"Unexpected error:\n{tb[-1500:]}")
        sys.exit(1)
