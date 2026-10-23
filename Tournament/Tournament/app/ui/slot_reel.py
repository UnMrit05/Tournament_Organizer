"""A slot-machine style reel: names glide down past a highlighted middle band and ease to a stop on the result."""

import random
import time
import tkinter as tk

from app.ui import gfx, theme
from app.ui.widgets import fit_text, text_width

VIEW_H = 152          # how tall the window onto the reel is (reference pixels)
BAND_H = 72           # the highlighted middle band
PITCH = 58            # distance between neighbouring names
SIDE_PAD = 0          # room left and right of the window (none: the reel is exactly as wide as its box)
FILLER = 16           # how many random names scroll by before the result
SPIN_SECONDS = 2.8
FRAME_MS = 15
POOL = 6              # how many text items are re-used while scrolling


def _ease_out(t):
    """Starts fast and slows down smoothly to a stop (0..1 in, 0..1 out)."""
    return 1 - (1 - t) ** 3


class SlotReel(tk.Canvas):
    """A reel that scrolls smoothly (time based, so it stays smooth even if a frame is late) and lands on a chosen value."""

    def __init__(self, parent, color_for=None, icon_for=None):
        """Sets up the canvas. color_for(value) picks a name's color; icon_for(value) gives a small picture shown beside the result."""
        self._view_h = theme.S(VIEW_H)
        super().__init__(parent, height=self._view_h, highlightthickness=0, bd=0, bg=theme.BG)
        self._color_for = color_for or (lambda value: theme.ACCENT_TEXT)
        self._icon_for = icon_for
        self._sequence = []
        self._pos = 0.0
        self._started = 0.0
        self._after_id = None
        self._on_done = None
        self._spinning = False
        self._rest_text = ""
        self._rest_color = None
        self._rest_icon = None
        self._images = []
        self._items = []
        self._icon_item = None
        self.bind("<Configure>", lambda e: self._paint())

    @property
    def spinning(self):
        """True while the reel is still moving."""
        return self._spinning

    # ---------- drawing ----------

    def _viewport(self):
        """Where the window onto the reel sits: (left, right, centre-x, centre-y)."""
        w = self.winfo_width()
        pad = theme.S(SIDE_PAD)
        return pad, w - pad, w / 2, self._view_h / 2

    def _paint(self):
        """Draws the frame, the highlighted band and the marker bars, then the names on top."""
        w = self.winfo_width()
        if w < 8:
            return
        self.delete("all")
        self._images = []
        left, right, cx, cy = self._viewport()
        band_h = theme.S(BAND_H)
        band_top = cy - band_h / 2
        self.create_rectangle(left, 0, right - 1, self._view_h - 1, fill=theme.PANEL_2, outline=theme.LINE)
        tint_top = theme.mix(theme.PANEL_2, theme.ACCENT, 0.36)
        tint_bottom = theme.mix(theme.PANEL_2, theme.ACCENT, 0.16)
        wash = gfx.vertical_swatch(int(right - left - 2), int(band_h), [(0, tint_top), (1, tint_bottom)])
        if wash is not None:
            self._images.append(wash)
            self.create_image(left + 1, band_top, image=wash, anchor="nw")
        else:
            self.create_rectangle(left + 1, band_top, right - 2, band_top + band_h, fill=tint_bottom, outline="")
        self.create_rectangle(left + 1, band_top, right - 2, band_top + band_h - 1, outline=theme.ACCENT_TEXT, width=2)
        bar_w, bar_h = theme.S(6), int(band_h - 2 * theme.S(14))
        bar = gfx.vertical_swatch(bar_w, bar_h, [(0, theme.ACCENT_HI), (1, theme.ACCENT_LO)])
        for x in (left + theme.S(10), right - theme.S(10) - bar_w):
            if bar is not None:
                self._images.append(bar)
                self.create_image(x, band_top + theme.S(14), image=bar, anchor="nw")
            else:
                self.create_rectangle(x, band_top + theme.S(14), x + bar_w, band_top + theme.S(14) + bar_h,
                                      fill=theme.ACCENT, outline="")
        self._items = [self.create_text(cx, -999, text="", anchor="center") for _ in range(POOL)]
        self._icon_item = self.create_image(-999, -999, anchor="center")
        if self._sequence and (self._spinning or self._rest_text == ""):
            self._draw_at(self._pos, icon=not self._spinning)
        else:
            self._draw_rest()

    def _font_for(self, distance):
        """The text size for a name this far from the middle: big in the band, smaller further out."""
        if distance < 0.45:
            return theme.fpx(theme.SEMIBOLD, 30)
        if distance < 1.2:
            return theme.fpx(theme.SEMIBOLD, 20)
        return theme.fpx(theme.SEMIBOLD, 16)

    def _draw_at(self, pos, icon=False):
        """Puts every visible name where it belongs when the reel has scrolled to position `pos`."""
        left, right, cx, cy = self._viewport()
        room = right - left - 2 * theme.S(16)
        base = int(pos // 1)
        pitch = theme.S(PITCH)
        shown = 0
        self.itemconfigure(self._icon_item, state="hidden")
        for k in range(base - 2, base + 4):
            if not 0 <= k < len(self._sequence) or shown >= POOL:
                continue
            distance = abs(pos - k)
            y = cy + (pos - k) * pitch
            if y < -pitch or y > self._view_h + pitch:
                continue
            value = self._sequence[k]
            strength = max(0.10, min(1.0, 1.15 - distance * 0.55))
            color = theme.mix(theme.PANEL_2, self._color_for(value), strength)
            font = self._font_for(distance)
            label = fit_text(str(value).upper(), font, room)
            item = self._items[shown]
            self.itemconfigure(item, text=label, fill=color, font=font, state="normal")
            self.coords(item, cx, y)
            shown += 1
            if icon and distance < 0.01 and self._icon_for is not None:
                self._place_icon(value, label, font, cx, y)
        for item in self._items[shown:]:
            self.itemconfigure(item, state="hidden")

    def _place_icon(self, value, label, font, cx, y):
        """Shows the value's little picture just left of its name."""
        picture = self._icon_for(value)
        if picture is None:
            return
        self._rest_icon = picture
        x = cx - text_width(font, label) / 2 - theme.S(16) - picture.width() / 2
        self.itemconfigure(self._icon_item, image=picture, state="normal")
        self.coords(self._icon_item, x, y)

    def _draw_rest(self):
        """Shows just one line of text in the middle band (for 'Press Spin' and similar)."""
        left, right, cx, cy = self._viewport()
        self.itemconfigure(self._icon_item, state="hidden")
        for i, item in enumerate(self._items):
            if i == 0 and self._rest_text:
                font = theme.fpx(theme.SEMIBOLD, 26)
                room = right - left - 2 * theme.S(16)
                self.itemconfigure(item, text=fit_text(self._rest_text.upper(), font, room),
                                   fill=self._rest_color or theme.TEXT, font=font, state="normal")
                self.coords(item, cx, cy)
            else:
                self.itemconfigure(item, state="hidden")

    # ---------- public ----------

    def set_static(self, text, color=None):
        """Stops any spin and just shows the given words in the middle band."""
        self._cancel()
        self._spinning = False
        self._sequence = []
        self._rest_text = text or ""
        self._rest_color = color
        if self.winfo_width() > 8:
            self._draw_rest()

    def spin(self, options, final_value, on_done=None):
        """Scrolls through random picks from the options and eases to a stop on the final value, then calls on_done."""
        self._cancel()
        if not options or final_value is None:
            self.set_static(final_value or "")
            if on_done:
                on_done()
            return
        names = []
        previous = None
        for _ in range(FILLER):
            pick = random.choice(options)
            if len(options) > 1:
                tries = 0
                while pick == previous and tries < 6:
                    pick = random.choice(options)
                    tries += 1
            names.append(pick)
            previous = pick
        self._sequence = names + [final_value]
        self._rest_text = ""
        self._on_done = on_done
        self._spinning = True
        self._started = time.monotonic()
        self._pos = -1.0
        self._draw_at(self._pos)
        self._after_id = self.after(FRAME_MS, self._tick)

    def _cancel(self):
        """Stops the animation timer if one's running."""
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _tick(self):
        """Moves the reel to where it should be by now and queues the next frame (or finishes up)."""
        self._after_id = None
        last = len(self._sequence) - 1
        t = (time.monotonic() - self._started) / SPIN_SECONDS
        if t >= 1:
            self._pos = float(last)
            self._spinning = False
            self._draw_at(self._pos, icon=True)
            if self._on_done:
                done, self._on_done = self._on_done, None
                done()
            return
        self._pos = -1.0 + (last + 1) * _ease_out(t)
        self._draw_at(self._pos)
        self._after_id = self.after(FRAME_MS, self._tick)

    def destroy(self):
        """Stops the animation before the reel goes away."""
        self._cancel()
        super().destroy()
