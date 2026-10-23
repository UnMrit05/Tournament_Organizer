"""The pop-up boxes: reset warning, unsaved-changes warning and the 'saved' notice. Each one blocks until you answer."""

import sys
import tkinter as tk

from app.ui import gfx, text, theme
from app.ui.widgets import GlassButton, HeaderBar

DIALOG_W = 464


def _veil(app):
    """Dims the app window behind a pop-up (where the system supports see-through windows). Gives back the dimmer or None."""
    if sys.platform not in ("win32", "darwin"):
        return None
    try:
        veil = tk.Toplevel(app)
        veil.overrideredirect(True)
        veil.configure(bg="#05060A")
        veil.attributes("-alpha", 0.6)
        veil.geometry(f"{app.winfo_width()}x{app.winfo_height()}+{app.winfo_rootx()}+{app.winfo_rooty()}")
        veil.transient(app)
        return veil
    except tk.TclError:
        return None


def ask(app, tone, title, message, ok_text, cancel_text=None):
    """Shows a pop-up and waits. tone is 'warn' (coral header) or 'good' (green header).
    Gives back True when OK is pressed, False for Cancel / Escape / closing it."""
    veil = _veil(app)
    top = tk.Toplevel(app)
    top.overrideredirect(True)
    top.configure(bg=theme.LINE)
    try:
        top.attributes("-topmost", True)
    except tk.TclError:
        pass
    result = {"ok": False}

    def finish(ok):
        """Records the answer and closes the pop-up (and the dimmer)."""
        result["ok"] = ok
        try:
            top.grab_release()
        except tk.TclError:
            pass
        top.destroy()
        if veil is not None:
            try:
                veil.destroy()
            except tk.TclError:
                pass

    width = theme.S(DIALOG_W)
    body = tk.Frame(top, bg=theme.DLG_BOTTOM)
    body.pack(fill="both", expand=True, padx=1, pady=1)

    warn = tone == "warn"
    fill = gfx.button_fill("danger" if warn else "ok")
    left, right = fill, fill
    header = HeaderBar(body, left, right, height=48, text=title.upper(), font=theme.FONT_BUTTON,
                       fg=theme.HEADER_INK, pad=24, icon="warn" if warn else "check", width=width)
    header.pack(fill="x")

    tk.Label(body, text=message, bg=theme.DLG_BOTTOM, fg=theme.TEXT, font=theme.fpx(theme.SANS, 20),
             justify="left", anchor="w", wraplength=width - 2 * theme.S(24) - 2).pack(
        fill="x", padx=theme.S(24), pady=theme.S(24))

    footer = tk.Frame(body, bg=theme.DLG_BOTTOM)
    footer.pack(fill="x", padx=theme.S(24), pady=(0, theme.S(24)))
    ok_btn = GlassButton(footer, ok_text, lambda: finish(True), kind="danger" if warn else "primary")
    ok_btn.pack(side="right")
    cancel_btn = None
    if cancel_text:
        cancel_btn = GlassButton(footer, cancel_text, lambda: finish(False), kind="secondary")
        cancel_btn.pack(side="right", padx=(0, theme.S(16)))

    length = theme.S(10)
    for relx, anchor in ((0, "sw"), (1, "se")):
        tk.Frame(top, bg=theme.TICK, width=length, height=1).place(relx=relx, rely=1, anchor=anchor)
        tk.Frame(top, bg=theme.TICK, width=1, height=length).place(relx=relx, rely=1, anchor=anchor)

    top.update_idletasks()
    x = app.winfo_rootx() + (app.winfo_width() - top.winfo_reqwidth()) // 2
    y = app.winfo_rooty() + (app.winfo_height() - top.winfo_reqheight()) // 2
    top.geometry(f"+{max(0, x)}+{max(0, y)}")
    top.bind("<Escape>", lambda e: finish(False))
    top.protocol("WM_DELETE_WINDOW", lambda: finish(False))
    top.lift()
    try:
        top.wait_visibility()
        top.grab_set()
    except tk.TclError:
        pass
    top.focus_force()
    (cancel_btn or ok_btn).focus_set()
    app.wait_window(top)
    return result["ok"]


def confirm_reset(app):
    """Warns that resetting wipes everything. True if the person pressed OK."""
    return ask(app, "warn", text.t("Reset Popup Title"), text.t("Reset Popup Text"),
               text.t("Button OK"), text.t("Button Cancel"))


def confirm_unsaved(app, home=False):
    """Warns that closing the app (or going back to the start, when home is True) throws away unsaved work.
    True if the person pressed OK."""
    message = text.t("Home Popup Text") if home else text.t("Unsaved Popup Text")
    return ask(app, "warn", text.t("Unsaved Popup Title"), message, text.t("Button OK"), text.t("Button Cancel"))


def notify_saved(app):
    """Tells the person their work was saved, and waits for OK."""
    ask(app, "good", text.t("Saved Popup Title"), text.t("Saved Popup Text"), text.t("Button OK"))
