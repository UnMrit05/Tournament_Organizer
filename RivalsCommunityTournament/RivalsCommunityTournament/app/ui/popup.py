"""A small transient popup for quick info (e.g. a captain's name next to
a team on the bracket) - not a real dialog, just a borderless window that
appears near the cursor and disappears on its own a moment later.
"""

import tkinter as tk

from app.ui import theme

AUTO_CLOSE_MS = 2200


class _Popup:
    """Tracks at most one open popup at a time so clicking around doesn't
    stack several of them on screen."""

    def __init__(self):
        self.window = None

    def show(self, widget, x_root, y_root, lines):
        self.close()
        top = tk.Toplevel(widget)
        top.overrideredirect(True)
        try:
            top.attributes("-topmost", True)
        except tk.TclError:
            pass
        frame = tk.Frame(top, bg=theme.PANEL_2, highlightbackground=theme.GOLD, highlightthickness=1)
        frame.pack()
        for i, line in enumerate(lines):
            fg = theme.GOLD if i == 0 else theme.DIM
            font = theme.FONT_NAME if i == 0 else theme.FONT_SMALL
            tk.Label(frame, text=line, fg=fg, bg=theme.PANEL_2, font=font,
                      justify="left", anchor="w").pack(anchor="w", padx=theme.S(10), pady=(theme.S(5), 0))
        tk.Frame(frame, bg=theme.PANEL_2, height=theme.S(5)).pack()
        top.geometry(f"+{x_root + 12}+{y_root + 12}")
        self.window = top
        top.after(AUTO_CLOSE_MS, lambda: self.close(top))

    def close(self, only_if=None):
        if self.window is None:
            return
        if only_if is not None and only_if is not self.window:
            return
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        self.window = None


def show_captain_popup(widget, event, team):
    """Show (or replace) a popup with a team's captain name, anchored near
    the click. `widget` owns the popup tracker (one popup per screen
    instance) via a lazily-created `_popup` attribute."""
    tracker = getattr(widget, "_popup_tracker", None)
    if tracker is None:
        tracker = _Popup()
        widget._popup_tracker = tracker
    tracker.show(widget, event.x_root, event.y_root,
                  [team.name, f"Captain: {team.captain.ign}"])
