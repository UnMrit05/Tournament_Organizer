"""A little popup that shows up near the cursor (like a captain's name on the bracket) and goes away by itself."""

import tkinter as tk

from app.ui import text, theme

AUTO_CLOSE_MS = 2200


class _Popup:
    """Keeps track of the one popup that's open, so they don't pile up."""

    def __init__(self):
        """Starts with no popup open."""
        self.window = None
        self._root = None
        self._click_bind_id = None

    def show(self, widget, x_root, y_root, lines):
        """Opens a borderless popup with the given lines of text near the mouse, replacing any old one."""
        self.close()
        top = tk.Toplevel(widget)
        top.overrideredirect(True)
        try:
            top.attributes("-topmost", True)
        except tk.TclError:
            pass
        frame = tk.Frame(top, bg=theme.ACCENT_TEXT)
        frame.pack()
        body = tk.Frame(frame, bg=theme.DLG_TOP)
        body.pack(padx=1, pady=1)
        for i, line in enumerate(lines):
            fg = theme.ACCENT_TEXT if i == 0 else theme.DIM
            font = theme.fpx(theme.SANS, 18) if i == 0 else theme.fpx(theme.SANS, 15)
            tk.Label(body, text=line, fg=fg, bg=theme.DLG_TOP, font=font,
                     justify="left", anchor="w").pack(anchor="w", padx=theme.S(16),
                                                      pady=(theme.S(8) if i == 0 else theme.S(4), 0))
        tk.Frame(body, bg=theme.DLG_TOP, height=theme.S(10)).pack()
        top.geometry(f"+{x_root + 12}+{y_root + 12}")
        self.window = top
        top.after(AUTO_CLOSE_MS, lambda: self.close(top))

        # Close on any click outside the popup. Bound after the click that
        # opened it has already been handled, so it doesn't close itself right away.
        self._root = widget.winfo_toplevel()
        self._click_bind_id = self._root.bind_all("<Button-1>", self._on_outside_click, add="+")

    def _on_outside_click(self, event):
        """Closes the popup when you click anywhere that isn't the popup."""
        if self.window is None:
            return
        try:
            clicked_toplevel = event.widget.winfo_toplevel()
        except tk.TclError:
            clicked_toplevel = None
        if clicked_toplevel is self.window:
            return  # click landed inside the popup itself - ignore
        self.close()

    def close(self, only_if=None):
        """Closes the popup (if it's still the one we expect) and stops listening for outside clicks."""
        if self.window is None:
            return
        if only_if is not None and only_if is not self.window:
            return
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        self.window = None
        if self._root is not None and self._click_bind_id is not None:
            try:
                self._root.unbind("<Button-1>", self._click_bind_id)
            except tk.TclError:
                pass
            self._root = None
            self._click_bind_id = None


def show_captain_popup(widget, x_root, y_root, team):
    """Pops up the team's name and captain next to the mouse position."""
    tracker = getattr(widget, "_popup_tracker", None)
    if tracker is None:
        tracker = _Popup()
        widget._popup_tracker = tracker
    tracker.show(widget, x_root, y_root,
                  [team.name, text.t("Captain Line", name=team.captain.twitch)])
