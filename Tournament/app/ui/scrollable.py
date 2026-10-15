"""A frame that scrolls up and down, and only grabs the mouse wheel while the pointer is over it."""

import tkinter as tk
from tkinter import ttk

from app.ui import theme


class ScrollableFrame(tk.Frame):
    """A scrolling area - put your stuff inside `.body`."""

    def __init__(self, parent, bg=None):
        """Sets up the canvas, scrollbar and inner body frame and hooks up the mouse wheel."""
        bg = bg or theme.BG
        super().__init__(parent, bg=bg)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                         style="Glass.Vertical.TScrollbar")
        self.body = tk.Frame(self.canvas, bg=bg)

        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_canvas_resize(self, event):
        """Keeps the inner body as wide as the canvas."""
        self.canvas.itemconfig(self._window, width=event.width)

    def _on_mousewheel(self, event):
        """Scrolls the content when the mouse wheel moves."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def ensure_visible(self, widget):
        """Scrolls just enough so the given widget is on screen."""
        self.update_idletasks()
        body_h = self.body.winfo_height()
        view_h = self.canvas.winfo_height()
        if body_h <= view_h or body_h <= 1:
            return
        top = widget.winfo_rooty() - self.body.winfo_rooty()
        bottom = top + widget.winfo_height()
        view_top = self.canvas.canvasy(0)
        if top < view_top:
            self.canvas.yview_moveto(max(0, top - 8) / body_h)
        elif bottom > view_top + view_h:
            self.canvas.yview_moveto(min(body_h - view_h, bottom - view_h + 8) / body_h)
