"""Starting point for the app. Run it with `python main.py`, or just double-click run.bat on Windows."""

import os
import sys
import traceback
from pathlib import Path

# Stops pygame printing its "hello" banner when it loads.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

CRASH_LOG = Path(__file__).resolve().parent / "saves" / "crash.log"


def hide_own_console():
    """On Windows, hides the black command window if it belongs to just this program
    (like when you double-click the file). If you started it from a terminal you're
    using, it leaves that terminal alone."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            return
        procs = (ctypes.c_uint * 4)()
        if ctypes.windll.kernel32.GetConsoleProcessList(procs, 4) <= 1:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def report_crash(text):
    """Saves the error to saves/crash.log and pops it up in a message box, since
    there's no visible command window to print it in."""
    try:
        CRASH_LOG.parent.mkdir(exist_ok=True)
        CRASH_LOG.write_text(text, encoding="utf-8")
    except OSError:
        pass
    try:
        if sys.stderr:
            print(text, file=sys.stderr)
    except Exception:
        pass
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Rivals Community Tournament",
            f"The app hit an error and had to close.\n\n{text[-1500:]}\n\n(Also saved to {CRASH_LOG})")
        root.destroy()
    except Exception:
        pass


def main():
    """Starts the app, and reports the error nicely if it crashes on startup."""
    hide_own_console()
    try:
        from app.app_state import TournamentApp
        TournamentApp().mainloop()
    except Exception:
        report_crash(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
