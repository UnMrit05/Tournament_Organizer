"""Drawing tools for lists and cards that live on one canvas: a scrolling canvas with a glass scrollbar,
little icon badges, rank tags, chips and a pop-up pick list. Drawing on a canvas instead of building
hundreds of widgets keeps screens quick to open and free of flicker."""

import tkinter as tk
from tkinter import ttk

from app.data.icons import get_role_glyph
from app.data.platforms import FALLBACK_TEXT
from app.data.ranks import strip_subdivision
from app.ui import gfx, theme
from app.ui.player_icons import platform_photo, role_photo
from app.ui.widgets import fit_text, line_height, text_width


# ---------- scrolling canvas ----------

class ScrollCanvas(tk.Frame):
    """A canvas that scrolls up and down with a glass scrollbar. Draw on .canvas; on_size(width) runs
    whenever the drawing area gets a new width so the screen can lay its content out again."""

    def __init__(self, parent, bg, on_size=None):
        """Builds the canvas and scrollbar and hooks up the mouse wheel (it only listens while the pointer is over it)."""
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0)
        self.on_size = on_size
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, yscrollincrement=theme.S(36))
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                       style="Glass.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self._size = (0, 0)
        self._content_h = 0
        self.canvas.bind("<Configure>", self._on_configure)
        for widget in (self, self.canvas, self.scrollbar):
            widget.bind("<Enter>", self._grab_wheel, add="+")
            widget.bind("<Leave>", self._release_wheel, add="+")

    def bar_width(self):
        """How wide the scrollbar is."""
        return self.scrollbar.winfo_reqwidth()

    def fit(self, width, height):
        """Tells the canvas how big its box is going to be, so the content can be drawn before anything shows on screen."""
        self._apply(max(1, int(width) - self.bar_width()), int(height))

    def _on_configure(self, event):
        """Takes the real size once the system has laid the canvas out."""
        self._apply(event.width, event.height)

    def _apply(self, width, height):
        """Remembers the new size and lets the screen redraw when the width really changed."""
        width_changed = abs(width - self._size[0]) > 1
        self._size = (width, height)
        if width_changed and self.on_size is not None:
            self.on_size(width)
        self._update_region()

    @property
    def width(self):
        """The width of the drawing area."""
        return self._size[0]

    @property
    def height(self):
        """The height of the visible part."""
        return self._size[1]

    def set_content_height(self, height):
        """Tells the canvas how tall everything drawn on it is, so it knows how far it can scroll."""
        self._content_h = int(height)
        self._update_region()

    def _update_region(self):
        """Sets the scrollable area to the content (never smaller than the visible part)."""
        width, height = self._size
        self.canvas.configure(scrollregion=(0, 0, max(1, width), max(self._content_h, height, 1)))

    def scroll_to_top(self):
        """Jumps back to the top."""
        self.canvas.yview_moveto(0)

    def ensure_visible(self, top, bottom, margin=None):
        """Scrolls just enough so the stretch from top to bottom (canvas coordinates) is on screen."""
        view = self._size[1]
        total = max(self._content_h, view)
        if view <= 0 or total <= view:
            return
        margin = theme.S(8) if margin is None else margin
        now = self.canvas.canvasy(0)
        if top - margin < now:
            target = top - margin
        elif bottom + margin > now + view:
            target = bottom + margin - view
        else:
            return
        self.canvas.yview_moveto(max(0, min(total - view, target)) / total)

    def _grab_wheel(self, _event=None):
        """Starts listening to the mouse wheel for this list."""
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _release_wheel(self, _event=None):
        """Stops listening to the wheel once the pointer has really left the list."""
        try:
            under = self.winfo_containing(*self.winfo_pointerxy())
        except (KeyError, tk.TclError):
            under = None
        if under is not None and str(under).startswith(str(self)):
            return
        self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, event):
        """Scrolls the content when the mouse wheel moves (nothing to do when it all fits)."""
        if self._content_h > self._size[1]:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ---------- clicking and hovering ----------

def make_hot(canvas, tag="hot"):
    """Makes anything carrying this tag show the hand cursor while the mouse is over it."""
    canvas.tag_bind(tag, "<Enter>", lambda e: canvas.configure(cursor="hand2"))
    canvas.tag_bind(tag, "<Leave>", lambda e: canvas.configure(cursor=""))


def on_click(canvas, handler):
    """Calls handler(tags, event) with the tags of whatever drawn item was clicked (one binding for the whole canvas)."""
    def fire(event):
        """Looks up what's under the mouse and passes its tags on."""
        items = canvas.find_withtag("current")
        if items:
            handler(canvas.gettags(items[0]), event)
    canvas.bind("<Button-1>", fire)


# ---------- little drawing helpers ----------

def box(canvas, x0, y0, x1, y1, fill, edge=None, tags=()):
    """Draws a flat rectangle with an optional 1 pixel edge. Gives back (edge item, fill item)."""
    if edge is None:
        return None, canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="", tags=tags)
    outer = canvas.create_rectangle(x0, y0, x1, y1, fill=edge, outline="", tags=tags)
    inner = canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill=fill, outline="", tags=tags)
    return outer, inner


def badge_side(size):
    """How big (in pixels) a role badge of this reference size is."""
    return theme.S(size) + 2 * theme.S(4) + 2


def draw_role_badge(canvas, x, y, role, size, bg, tags=()):
    """Draws a small tinted square with the role's icon, its top-left corner at (x, y). Gives back the side length."""
    side = badge_side(size)
    color = theme.ROLE_COLOR.get(role, theme.DIM)
    box(canvas, x, y, x + side, y + side, theme.mix(bg, color, 0.20), theme.mix(bg, color, 0.70), tags)
    photo = role_photo(role, size)
    if photo is not None:
        canvas.create_image(x + side / 2, y + side / 2, image=photo, tags=tags)
    else:
        canvas.create_text(x + side / 2, y + side / 2, text=get_role_glyph(role),
                           fill=theme.ROLE_TEXT.get(role, theme.DIM), font=theme.font(theme.SANS, max(8, size - 5)),
                           tags=tags)
    return side


def platform_width(platform, size):
    """How wide the platform icon (or its text tag) is."""
    if not platform:
        return 0
    if platform_photo(platform, size) is not None:
        return theme.S(size)
    return text_width(theme.fpx(theme.SEMIBOLD, 10), FALLBACK_TEXT[platform]) + 2 * theme.S(5)


def draw_platform(canvas, x, y, platform, size, tags=()):
    """Draws the platform icon (or a small colored PS / XB / PC tag) with its top-left corner at (x, y). Gives back its width."""
    if not platform:
        return 0
    px = theme.S(size)
    photo = platform_photo(platform, size)
    if photo is not None:
        canvas.create_image(x, y, image=photo, anchor="nw", tags=tags)
        return px
    font = theme.fpx(theme.SEMIBOLD, 10)
    width = platform_width(platform, size)
    height = line_height(font) + 2 * theme.S(2)
    top = y + (px - height) / 2
    canvas.create_rectangle(x, top, x + width, top + height, fill=theme.PLATFORM_COLOR.get(platform, theme.DIM),
                            outline="", tags=tags)
    canvas.create_text(x + width / 2, top + height / 2, text=FALLBACK_TEXT[platform], fill=theme.HEADER_INK, font=font,
                       tags=tags)
    return width


def rank_tag_width(rank, font):
    """How wide a rank tag (colored square plus the rank) is."""
    return theme.S(8) + theme.S(6) + text_width(font, rank)


def draw_rank_tag(canvas, x, y_mid, rank, font, tags=()):
    """Draws a square in the rank tier's color followed by the rank text, vertically centered on y_mid. Gives back its width."""
    color = theme.TIER_COLOR.get(strip_subdivision(rank), theme.DIM)
    side = theme.S(8)
    canvas.create_rectangle(x, y_mid - side / 2, x + side, y_mid + side / 2, fill=color, outline="", tags=tags)
    canvas.create_text(x + side + theme.S(6), y_mid, text=rank, anchor="w", fill=theme.DIM, font=font, tags=tags)
    return rank_tag_width(rank, font)


def chip_width(label, font, dot=False):
    """How wide a chip with this label is."""
    extra = theme.S(8 + 8) if dot else 0
    return text_width(font, label) + 2 * theme.S(12) + 2 + extra


def draw_chip(canvas, x, y, label, font, fill, edge, fg, dot=None, tags=(), height=None):
    """Draws a small rectangular tag (like the pool chips) with its top-left corner at (x, y). Gives back (width, height)."""
    height = height or theme.S(28)
    width = chip_width(label, font, dot is not None)
    box(canvas, x, y, x + width, y + height, fill, edge, tags)
    left = x + 1 + theme.S(12)
    if dot is not None:
        side = theme.S(8)
        canvas.create_rectangle(left, y + height / 2 - side / 2, left + side, y + height / 2 + side / 2,
                                fill=dot, outline="", tags=tags)
        left += side + theme.S(8)
    canvas.create_text(left, y + height / 2, text=label, anchor="w", fill=fg, font=font, tags=tags)
    return width, height


def draw_text(canvas, x, y, label, font, fill, room, anchor="w", tags=()):
    """Draws one line of text, trimmed with an ellipsis if it's wider than `room`. Gives back the item."""
    return canvas.create_text(x, y, text=fit_text(label, font, room), anchor=anchor, fill=fill, font=font, tags=tags)


def draw_gradient(canvas, x, y, w, h, left, right, dust=True, tags=()):
    """Draws a left-to-right colored strip (like a team header). Gives back the item."""
    img = gfx.gradient_bar(int(w), int(h), left, right, dust)
    if img is not None:
        return canvas.create_image(x, y, image=img, anchor="nw", tags=tags)
    return canvas.create_rectangle(x, y, x + w, y + h, fill=left, outline="", tags=tags)


# ---------- hover hints for drawn things ----------

class TagTip:
    """Little hover hints for things drawn on a canvas: tag an item with a name, register the words for that name,
    and the hint shows when the mouse rests on it."""

    def __init__(self, canvas, delay=450):
        """Starts with no hints registered."""
        self.canvas = canvas
        self.delay = delay
        self._job = None
        self._tip = None
        self._pos = (0, 0)

    def add(self, tag, words):
        """Shows `words` when the mouse rests on anything carrying this tag."""
        self.canvas.tag_bind(tag, "<Enter>", lambda e, w=words: self._schedule(e, w), add="+")
        self.canvas.tag_bind(tag, "<Leave>", lambda e: self.hide(), add="+")
        self.canvas.tag_bind(tag, "<ButtonPress-1>", lambda e: self.hide(), add="+")

    def _schedule(self, event, words):
        """Starts the little wait before the hint appears."""
        self.hide()
        self._pos = (event.x_root, event.y_root)
        self._job = self.canvas.after(self.delay, lambda: self._show(words))

    def _show(self, words):
        """Pops the hint up just under the mouse."""
        self._job = None
        try:
            tip = tk.Toplevel(self.canvas)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            frame = tk.Frame(tip, bg=theme.ACCENT_TEXT if theme.MODE == "light" else theme.ACCENT, padx=1, pady=1)
            frame.pack()
            tk.Label(frame, text=words, bg=theme.PANEL, fg=theme.TEXT, font=theme.FONT_SMALL, padx=theme.S(8),
                     pady=theme.S(3)).pack()
            tip.geometry(f"+{max(0, self._pos[0] - tip.winfo_reqwidth() // 2)}+{self._pos[1] + theme.S(18)}")
            self._tip = tip
        except tk.TclError:
            self._tip = None

    def hide(self):
        """Takes the hint away (or cancels it before it shows)."""
        if self._job is not None:
            try:
                self.canvas.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None


# ---------- pop-up pick list ----------

class DropMenu:
    """A tiny pop-up list of choices that opens under (or over) a box, and closes when you pick something or click elsewhere."""

    def __init__(self):
        """Starts with nothing open."""
        self.top = None
        self._root = None
        self._bind_id = None
        self._arm_job = None

    def open(self, widget, x_root, top_root, bottom_root, width, options, current, on_pick):
        """Opens the list under the box (whose top and bottom edges are given in screen coordinates), or over it if there's no room."""
        self.close()
        top = tk.Toplevel(widget)
        top.overrideredirect(True)
        try:
            top.attributes("-topmost", True)
        except tk.TclError:
            pass
        edge = tk.Frame(top, bg=theme.ACCENT_TEXT)
        edge.pack()
        inner = tk.Frame(edge, bg=theme.PANEL_2)
        inner.pack(padx=1, pady=1)
        pad = max(1, (theme.S(26) - line_height(theme.FONT_SMALL)) // 2)
        hover = theme.mix(theme.PANEL_2, theme.ACCENT, 0.35)

        def pick(value):
            """Hands the choice back and closes the list."""
            self.close()
            on_pick(value)

        for option in options:
            on = option == current
            label = tk.Label(inner, text=option, anchor="w", bg=theme.ACCENT if on else theme.PANEL_2,
                             fg=theme.ACCENT_INK if on else theme.TEXT, font=theme.FONT_SMALL, padx=theme.S(10),
                             width=max(1, width // max(1, text_width(theme.FONT_SMALL, "0"))), cursor="hand2")
            label.pack(fill="x", ipady=pad)
            if not on:
                label.bind("<Enter>", lambda e, w=label: w.configure(bg=hover))
                label.bind("<Leave>", lambda e, w=label: w.configure(bg=theme.PANEL_2))
            label.bind("<Button-1>", lambda e, v=option: pick(v))
        top.update_idletasks()
        height = top.winfo_reqheight()
        y = bottom_root + 2
        if y + height > widget.winfo_screenheight():
            y = max(0, top_root - height - 2)
        top.geometry(f"+{int(x_root)}+{int(y)}")
        self.top = top
        self._root = widget.winfo_toplevel()
        # Listen for outside clicks a moment later, so the click that opened the list doesn't close it again.
        self._arm_job = self._root.after(60, self._arm)

    def _arm(self):
        """Starts watching for clicks outside the list."""
        self._arm_job = None
        if self.top is not None and self._root is not None:
            self._bind_id = self._root.bind("<Button-1>", self._outside, add="+")

    def _outside(self, event):
        """Closes the list when you click anywhere that isn't the list itself."""
        if self.top is None:
            return
        try:
            clicked = event.widget.winfo_toplevel()
        except (tk.TclError, KeyError):
            clicked = None
        if clicked is not self.top:
            self.close()

    def close(self):
        """Closes the list if it's open."""
        if self._arm_job is not None and self._root is not None:
            try:
                self._root.after_cancel(self._arm_job)
            except tk.TclError:
                pass
            self._arm_job = None
        if self.top is not None:
            try:
                self.top.destroy()
            except tk.TclError:
                pass
            self.top = None
        if self._root is not None and self._bind_id is not None:
            try:
                self._root.unbind("<Button-1>", self._bind_id)
            except tk.TclError:
                pass
        self._root = None
        self._bind_id = None
