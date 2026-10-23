"""The base for every screen: one big canvas that paints the background, the header (title + step tracker) and the watermark,
and lines the screen's widgets up on the 12-column grid with the same margins and gutters everywhere."""

import time
import tkinter as tk

from app.ui import gfx, text, theme
from app.ui.widgets import GlassButton, fit_text, text_width

STEP_KEYS = ["Step Draft", "Step Type", "Step Spin", "Step Seed", "Step Bracket", "Step Crown"]
RESIZE_DELAY_MS = 60       # how long to wait for a window drag to settle before redrawing the background
DRAG_WINDOW_S = 0.25       # sizes that arrive closer together than this count as a drag
POP_DELAY_MS = 500         # how long the big headings wait before their pop-in


class Stage(tk.Canvas):
    """A full-window canvas. Subclass it, build widgets on it, and register where each one goes."""

    STEP = None            # which of the 6 tracker steps is current (None hides the tracker)
    WATERMARK = "center"   # where 'Made by ...' sits: left, center or right
    HAS_HEADER = True
    HEADER_LINE = True     # the thin line under the header (off on the Start screen)
    HAS_HOME = True        # the Home button at the left end of the bottom row (not on the Start screen)

    def __init__(self, parent, app, name):
        """Sets up the canvas, the header items, the watermark and the resize handling."""
        super().__init__(parent, bg=theme.BG, highlightthickness=0, bd=0)
        self.app = app
        self.screen_name = name
        self._size = (0, 0)
        self._layouts = []
        self._rects = {}
        self._bg_photo = None
        self._bg_job = None
        self._last_resize = 0.0
        self._on_rect = {}
        self._home_btn = None
        self._line_photos = {}
        self._notes = {}
        # The big headings only pop in when you actually arrive here, not when the colors or window size change.
        self.intro = bool(getattr(app, "intro_pending", True))
        self._bg_item = self.create_image(0, 0, anchor="nw")
        self._title_item = self.create_text(0, 0, anchor="w", text="", fill=theme.TEXT, font=theme.FONT_TITLE)
        self._title_text = ""
        self._hair_item = self.create_image(0, 0, anchor="nw")
        self._step_items = []
        self._build_steps()
        self._wm_item = self.create_text(0, 0, text=text.t("Credit"), fill=theme.FAINT,
                                         font=theme.fpx(theme.SANS, 12))
        self.bind("<Configure>", self._on_configure)
        if self.HAS_HOME:
            self.add_home()

    # ---------- grid ----------

    def margin(self):
        """The space between the window edge and the content."""
        return theme.S(theme.MARGIN)

    def gutter(self):
        """The space between neighbours."""
        return theme.S(theme.GUTTER)

    def column_width(self):
        """How wide one of the 12 grid columns is right now."""
        w = self._size[0]
        return (w - 2 * self.margin() - (theme.COLUMNS - 1) * self.gutter()) / theme.COLUMNS

    def col_x(self, col):
        """Where grid column number `col` (0-11) starts on the left."""
        return int(round(self.margin() + col * (self.column_width() + self.gutter())))

    def span_w(self, span):
        """How wide a block spanning `span` columns is."""
        return int(round(span * self.column_width() + (span - 1) * self.gutter()))

    def header_top(self):
        """The y of the header row."""
        return self.margin()

    def body_top(self):
        """The y where the content under the header starts."""
        top = self.margin()
        return top + theme.S(theme.HEADER_H) + self.gutter() if self.HAS_HEADER else top

    def footer_top(self):
        """The y of the bottom button row."""
        return self._size[1] - self.margin() - theme.S(theme.FOOTER_H)

    def body_bottom(self, footer=True):
        """The y where the content stops (above the footer row when there is one)."""
        if footer:
            return self.footer_top() - self.gutter()
        return self._size[1] - self.margin()

    def right_edge(self):
        """The x of the right content edge."""
        return self._size[0] - self.margin()

    # ---------- state that survives a repaint (light/dark switch) ----------

    def capture_state(self):
        """Gives back whatever the screen needs to remember when it is rebuilt after a mode change."""
        return {}

    def restore_state(self, state):
        """Puts back what capture_state() gave."""

    def is_busy(self):
        """Says whether the screen is in the middle of something (like a spin) that mustn't be interrupted."""
        return False

    # ---------- registering things ----------

    def put(self, widget, rect_fn, on_rect=None):
        """Puts a widget on the canvas. rect_fn() gives back (x, y, w, h) and is re-run on every resize.
        on_rect(w, h), if given, runs whenever the widget's box changes size (before anything is drawn on screen)."""
        item = self.create_window(0, 0, window=widget, anchor="nw")
        self._layouts.append(("window", item, rect_fn))
        if on_rect is not None:
            self._on_rect[item] = on_rect
        return item

    def draw_panel(self, rect_fn, stripe=True, ticks=True, fill=None, border=None):
        """Draws a glass panel straight on the canvas: a thin border, the panel color, an aurora stripe along the
        top and gold ticks in the bottom corners. Gives back a function that says where the room inside it is (x, y, w, h)."""
        fill = fill or theme.PANEL
        border = border or theme.LINE
        outer = self.create_rectangle(0, 0, 1, 1, fill=border, outline="")
        inner = self.create_rectangle(0, 0, 1, 1, fill=fill, outline="")
        band = theme.S(2) if stripe else 0
        stripe_item = self.create_image(0, 0, anchor="nw") if stripe else None
        tick_items = [self.create_line(0, 0, 1, 1, fill=theme.TICK) for _ in range(4)] if ticks else []

        def lay():
            """Moves the border, fill, stripe and ticks to where the panel is now."""
            x, y, w, h = (int(v) for v in rect_fn())
            self.coords(outer, x, y, x + w, y + h)
            self.coords(inner, x + 1, y + 1, x + w - 1, y + h - 1)
            if stripe_item is not None:
                img = gfx.aurora_bar(max(2, w - 2), band)
                if img is not None:
                    self._line_photos[("stripe", stripe_item)] = img
                    self.itemconfigure(stripe_item, image=img)
                self.coords(stripe_item, x + 1, y + 1)
            if tick_items:
                length = theme.S(10)
                bottom = y + h - 1
                self.coords(tick_items[0], x, bottom, x + length, bottom)
                self.coords(tick_items[1], x, bottom - length, x, bottom)
                self.coords(tick_items[2], x + w - 1 - length, bottom, x + w - 1, bottom)
                self.coords(tick_items[3], x + w - 1, bottom - length, x + w - 1, bottom)

        self._layouts.append(("call", None, lay))

        def room():
            """The space inside the panel, under the stripe: (x, y, w, h)."""
            x, y, w, h = rect_fn()
            return (x + 1, y + 1 + band, w - 2, h - 2 - band)
        return room

    def add_home(self):
        """Puts the Home button at the left end of the bottom row. It goes back to the start screen after the unsaved-changes warning."""
        btn = GlassButton(self, text.t("Button Home"), self.app.request_home, kind="secondary")
        self.put(btn, lambda: (self.margin(), self.footer_top(), btn.pixel_width, btn.pixel_height))
        self._home_btn = btn
        return btn

    def footer_left(self):
        """The x where the rest of the bottom row can start (just after the Home button when there is one)."""
        if self._home_btn is None:
            return self.margin()
        return self.margin() + self._home_btn.pixel_width + self.gutter()

    def hook(self, fn):
        """Registers a function to run on every layout pass (for custom drawing)."""
        self._layouts.append(("call", None, fn))

    def set_title(self, title):
        """Changes the big heading in the header."""
        self._title_text = (title or "").upper()
        self._place_title()

    def section(self, label, rect_fn, trailing=None, reserve=None):
        """A section title: a small accent swatch, an uppercase label, a fading aurora line, and an optional widget on the right.
        rect_fn() gives back (x, y, w) for the row. reserve() can give a width to keep free at the right end
        (for something drawn there by the screen itself)."""
        swatch_px = theme.S(8)
        swatch_img = gfx.swatch(swatch_px, theme.ACCENT_HI, theme.ACCENT_LO)
        sw_item = self.create_image(0, 0, anchor="nw", image=swatch_img) if swatch_img is not None else \
            self.create_rectangle(0, 0, swatch_px, swatch_px, fill=theme.ACCENT, outline="")
        self._line_photos[("sw", sw_item)] = swatch_img
        txt_item = self.create_text(0, 0, anchor="w", text=label.upper(), fill=theme.DIM, font=theme.FONT_SECTION)
        line_item = self.create_image(0, 0, anchor="nw")
        trail_item = self.create_window(0, 0, window=trailing, anchor="nw") if trailing is not None else None
        row_h = theme.S(28)
        state = {"label": label}

        def lay():
            """Positions the swatch, label, line and trailing widget for the current size."""
            x, y, w = rect_fn()
            self.coords(sw_item, x, y + (row_h - swatch_px) // 2)
            tx = x + swatch_px + theme.S(8)
            right = x + w
            if trail_item is not None:
                tw, th = trailing.winfo_reqwidth(), trailing.winfo_reqheight()
                self.coords(trail_item, right - tw, y + (row_h - th) // 2)
                self.itemconfigure(trail_item, width=tw, height=th)
                right -= tw + theme.S(12)
            if reserve is not None:
                right -= reserve() + theme.S(12)
            room = right - tx
            shown = fit_text(state["label"].upper(), theme.FONT_SECTION, room)
            self.itemconfigure(txt_item, text=shown)
            self.coords(txt_item, tx, y + row_h // 2)
            used = text_width(theme.FONT_SECTION, shown)
            line_x = tx + used + theme.S(12)
            line_w = int(right - line_x)
            if line_w > 4:
                img = gfx.fade_line(line_w, gfx.sample_background(line_x, y + row_h // 2), alpha=0.7)
                if img is not None:
                    self._line_photos[("ln", line_item)] = img
                    self.itemconfigure(line_item, image=img, state="normal")
                    self.coords(line_item, line_x, y + row_h // 2)
            else:
                self.itemconfigure(line_item, state="hidden")

        self._layouts.append(("call", None, lay))
        return state

    def text_note(self, content, rect_fn, color=None, font=None, anchor="w"):
        """A line of plain text drawn straight on the background. rect_fn() gives back (x, y, w)."""
        item = self.create_text(0, 0, anchor=anchor, text=content, fill=color or theme.DIM,
                                font=font or theme.FONT_NOTE)
        self._notes[item] = content

        def lay():
            """Places the line and trims it to fit."""
            x, y, w = rect_fn()
            self.itemconfigure(item, text=fit_text(self._notes[item], font or theme.FONT_NOTE, w))
            self.coords(item, x, y)
        self._layouts.append(("call", None, lay))
        return item

    def set_note(self, item, content):
        """Changes a note's words and refits it."""
        self._notes[item] = content
        self.relayout()

    # ---------- header ----------

    def _build_steps(self):
        """Creates the little numbered boxes of the progress tracker (display only)."""
        if self.STEP is None or not self.HAS_HEADER:
            return
        for i in range(len(STEP_KEYS)):
            rect = self.create_rectangle(0, 0, 1, 1, width=1)
            num = self.create_text(0, 0, text=str(i + 1), font=theme.FONT_STEP)
            line = self.create_line(0, 0, 1, 1, width=1) if i else None
            label = self.create_text(0, 0, anchor="w", text=text.t(STEP_KEYS[i]).upper(),
                                     fill=theme.TEXT, font=theme.FONT_SECTION) if i == self.STEP else None
            self._step_items.append((rect, num, line, label))

    def toolbar_width(self):
        """How wide the top-right toolbar is (5 square buttons with gaps)."""
        return 5 * theme.S(theme.SQUARE) + 4 * theme.S(theme.SP_2)

    def _place_steps(self):
        """Lines the tracker up against the left of the toolbar."""
        if not self._step_items:
            return
        node = theme.S(24)
        gap = theme.S(8)
        link = theme.S(16)
        label_w = 0
        cur = self._step_items[self.STEP]
        if cur[3] is not None:
            label_w = text_width(theme.FONT_SECTION, text.t(STEP_KEYS[self.STEP]).upper()) + gap
        total = len(self._step_items) * node + (len(self._step_items) - 1) * (2 * gap + link) + label_w
        x = self._size[0] - self.margin() - self.toolbar_width() - self.gutter() - total
        mid = self.header_top() + theme.S(theme.HEADER_H) // 2
        self._steps_left = x
        for i, (rect, num, line, label) in enumerate(self._step_items):
            if line is not None:
                self.coords(line, x + gap, mid, x + gap + link, mid)
                self.itemconfigure(line, fill=theme.LINE)
                x += 2 * gap + link
            self.coords(rect, x, mid - node // 2, x + node - 1, mid + node // 2 - 1)
            self.coords(num, x + node / 2, mid)
            if i < self.STEP:
                self.itemconfigure(rect, fill=theme.ACCENT, outline=theme.ACCENT_EDGE)
                self.itemconfigure(num, fill=theme.ACCENT_INK)
            elif i == self.STEP:
                self.itemconfigure(rect, fill=theme.PANEL_2, outline=theme.ACCENT_TEXT)
                self.itemconfigure(num, fill=theme.ACCENT_TEXT)
            else:
                self.itemconfigure(rect, fill=theme.PANEL_2, outline=theme.LINE)
                self.itemconfigure(num, fill=theme.FAINT)
            x += node
            if label is not None:
                self.coords(label, x + gap, mid)
                x += label_w

    def _place_title(self):
        """Puts the heading at the left of the header and trims it to the room left of the tracker."""
        if not self.HAS_HEADER or self._size[0] < 10:
            return
        limit = getattr(self, "_steps_left", self._size[0] - self.margin() - self.toolbar_width()) - self.gutter()
        room = limit - self.margin()
        self.itemconfigure(self._title_item, text=fit_text(self._title_text, theme.FONT_TITLE, room))
        self.coords(self._title_item, self.margin(), self.header_top() + theme.S(theme.HEADER_H) // 2)

    def _place_header_line(self):
        """The thin fading aurora line under the header."""
        if not self.HAS_HEADER or not self.HEADER_LINE:
            return
        y = self.header_top() + theme.S(theme.HEADER_H) + theme.S(8)
        w = self._size[0] - 2 * self.margin()
        img = gfx.fade_line(w, gfx.sample_background(self._size[0] / 2, y), alpha=0.6)
        if img is not None:
            self._line_photos["hair"] = img
            self.itemconfigure(self._hair_item, image=img)
            self.coords(self._hair_item, self.margin(), y)

    def _place_watermark(self):
        """Puts the credit in the bottom corner or middle for this screen."""
        w, h = self._size
        y = h - theme.S(5)
        if self.WATERMARK == "left":
            self.itemconfigure(self._wm_item, anchor="sw")
            self.coords(self._wm_item, self.margin(), y)
        elif self.WATERMARK == "right":
            self.itemconfigure(self._wm_item, anchor="se")
            self.coords(self._wm_item, w - self.margin(), y)
        else:
            self.itemconfigure(self._wm_item, anchor="s")
            self.coords(self._wm_item, w / 2, y)

    # ---------- layout ----------

    def _on_configure(self, event):
        """Re-lays everything out when the canvas changes size, and refreshes the background shortly after."""
        if (event.width, event.height) == self._size:
            return
        self.relayout(event.width, event.height)

    def relayout(self, width=None, height=None):
        """Moves every registered widget, note and header piece to where the grid says it should be."""
        if width is not None:
            changed = (width, height) != self._size
            self._size = (width, height)
        else:
            changed = False
        if self._size[0] < 10 or self._size[1] < 10:
            return
        self._place_steps()
        self._place_title()
        self._place_watermark()
        for kind, item, fn in self._layouts:
            if kind == "window":
                x, y, w, h = fn()
                rect = (int(x), int(y), int(w), int(h))
                if self._rects.get(item) != rect:
                    self._rects[item] = rect
                    self.coords(item, rect[0], rect[1])
                    self.itemconfigure(item, width=max(1, rect[2]), height=max(1, rect[3]))
                    callback = self._on_rect.get(item)
                    if callback is not None:
                        callback(rect[2], rect[3])
            else:
                fn()
        if changed or self._bg_photo is None:
            self._draw_background(first=self._bg_photo is None)
        self.tag_lower(self._bg_item)

    def _draw_background(self, first=False):
        """Paints the background straight away (first time, a single jump like full screen, or a size we already have),
        or after a short pause while the window is being dragged."""
        if self._bg_job is not None:
            self.after_cancel(self._bg_job)
            self._bg_job = None
        now = time.monotonic()
        dragging = now - self._last_resize < DRAG_WINDOW_S
        self._last_resize = now
        if first or not dragging or gfx.background_ready(*self._size):
            self._paint_background()
        else:
            self._bg_job = self.after(RESIZE_DELAY_MS, self._paint_background)

    def _paint_background(self):
        """Draws the background picture for the current size and re-blends the thin lines into it."""
        self._bg_job = None
        w, h = self._size
        photo = gfx.background(w, h)
        if photo is not None:
            self._bg_photo = photo
            self.itemconfigure(self._bg_item, image=photo)
        else:
            self._bg_photo = False
            self.configure(bg=theme.BG)
        self._place_header_line()
        for kind, _item, fn in self._layouts:
            if kind == "call":
                fn()
        self.tag_lower(self._bg_item)

    def destroy(self):
        """Stops the pending background job before the canvas goes away."""
        if self._bg_job is not None:
            try:
                self.after_cancel(self._bg_job)
            except tk.TclError:
                pass
            self._bg_job = None
        super().destroy()
