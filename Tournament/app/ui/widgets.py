"""The building blocks every screen shares: gradient buttons, toolbar buttons, tooltips, the glass panel with its aurora stripe and gold corner ticks, and the colored header bar."""

import tkinter as tk
from tkinter import font as tkfont

from app.ui import gfx, theme

_font_cache = {}
_width_cache = {}
_height_cache = {}
_WIDTH_CACHE_LIMIT = 40000


def _font_key(font):
    """Turns a font description into something that can be used as a dictionary key."""
    return tuple(font) if isinstance(font, (list, tuple)) else font


def font_object(font):
    """Gives back the real tkinter Font for a font description (made once, then remembered)."""
    key = _font_key(font)
    measure = _font_cache.get(key)
    if measure is None:
        measure = tkfont.Font(font=font)
        _font_cache[key] = measure
    return measure


def text_width(font, text):
    """How many pixels wide this text is in this font (remembered, so the same words are never measured twice)."""
    key = (_font_key(font), text)
    width = _width_cache.get(key)
    if width is None:
        if len(_width_cache) > _WIDTH_CACHE_LIMIT:
            _width_cache.clear()
        width = font_object(font).measure(text)
        _width_cache[key] = width
    return width


def line_height(font):
    """How tall one line of text in this font is, in pixels."""
    key = _font_key(font)
    height = _height_cache.get(key)
    if height is None:
        height = font_object(font).metrics("linespace")
        _height_cache[key] = height
    return height


def fit_text(text, font, max_width):
    """Chops text with an ellipsis so it fits inside max_width pixels."""
    if max_width <= 0:
        return ""
    if text_width(font, text) <= max_width:
        return text
    low, high = 1, len(text)
    while low < high:
        mid = (low + high + 1) // 2
        if text_width(font, text[:mid] + "…") <= max_width:
            low = mid
        else:
            high = mid - 1
    return text[:low] + "…"


class GlassButton(tk.Button):
    """A gradient button with an exact pixel size. Kinds: primary (accent), secondary (glass), danger, ok."""

    def __init__(self, parent, text="", command=None, kind="secondary", width=None, height=None,
                 icon=None, font=None, pad=24, minimum=96):
        """Draws the button face for its size and kind, or falls back to a flat button without Pillow."""
        self.kind = kind
        self._label_font = font or theme.FONT_BUTTON
        label = text.upper()
        self._ph = theme.S(height or theme.FOOTER_H)
        if width is None:
            self._pw = max(theme.S(minimum), text_width(self._label_font, label) + 2 * theme.S(pad)
                          + (theme.S(20) if icon == "swatch" else 0))
        else:
            self._pw = theme.S(width)
        self._icon = icon
        self._enabled = True
        ink = gfx.button_ink(kind)
        self._ink = ink
        self._flat_px = tk.PhotoImage(width=1, height=1)
        face = gfx.button(self._pw, self._ph, kind, "normal", icon)
        flat_bg = self._flat_color()
        self._command = command
        super().__init__(parent, text=label, command=self._invoke_command, image=face or self._flat_px,
                         compound="center", width=self._pw, height=self._ph, font=self._label_font,
                         fg=ink, activeforeground=ink,
                         bg=flat_bg, activebackground=flat_bg, relief="flat", bd=0,
                         highlightthickness=0, padx=0, pady=0, takefocus=0, cursor="hand2")
        self._has_pictures = face is not None
        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")

    def _invoke_command(self):
        """Runs the button's command, unless the button is switched off."""
        if self._enabled and self._command is not None:
            self._command()

    def _flat_color(self):
        """The plain fill used when there's no Pillow to draw the gradient."""
        if self.kind == "primary":
            return theme.ACCENT
        if self.kind == "danger":
            return gfx.button_fill("danger")
        if self.kind == "ok":
            return gfx.button_fill("ok")
        return theme.BTN_TOP

    def _show(self, state):
        """Puts the picture for this state on the button (hover, normal or disabled)."""
        if not self._has_pictures:
            return
        face = gfx.button(self._pw, self._ph, self.kind, state, self._icon)
        if face is not None:
            tk.Button.configure(self, image=face)

    def _on_enter(self, _event=None):
        """Brightens the button when the mouse is over it."""
        if self._enabled:
            self._show("hover")

    def _on_leave(self, _event=None):
        """Puts the button back to normal when the mouse leaves."""
        if self._enabled:
            self._show("normal")

    def configure(self, cnf=None, **kw):
        """Same as a normal button's configure, but changing the state also swaps the picture."""
        if cnf:
            kw = dict(cnf, **kw)
        if "state" in kw:
            # The button is never really disabled in Tk (that would stipple the picture on some systems);
            # it just stops reacting and shows its dimmed face.
            self._enabled = kw.pop("state") != "disabled"
            kw["fg"] = self._ink if self._enabled else theme.mix(self._ink, theme.PANEL, 0.5)
            kw["activeforeground"] = kw["fg"]
            kw["cursor"] = "hand2" if self._enabled else "arrow"
            self._show("normal" if self._enabled else "disabled")
        if "command" in kw:
            self._command = kw.pop("command")
        if "text" in kw and isinstance(kw["text"], str):
            kw["text"] = kw["text"].upper()
        return tk.Button.configure(self, **kw)

    config = configure

    def refresh(self):
        """Redraws the button face (after the mode or accent color changed)."""
        self._show("normal" if self._enabled else "disabled")

    def resize_to(self, pixels):
        """Changes the button's width (in real pixels) and redraws its face, for buttons that fill a box of any size."""
        pixels = max(theme.S(40), int(pixels))
        if pixels == self._pw:
            return
        self._pw = pixels
        tk.Button.configure(self, width=pixels)
        self._show("normal" if self._enabled else "disabled")

    def set_enabled(self, enabled):
        """Turns the button on or off."""
        self.configure(state="normal" if enabled else "disabled")

    @property
    def enabled(self):
        """Says whether the button can be clicked right now."""
        return self._enabled

    @property
    def pixel_width(self):
        """The button's width in real pixels."""
        return self._pw

    @property
    def pixel_height(self):
        """The button's height in real pixels."""
        return self._ph


class ToolButton(GlassButton):
    """A small square toolbar button with a drawn icon (and a hover tip)."""

    def __init__(self, parent, icon, command=None, tip=""):
        """Makes the 32 px square button for the icon."""
        super().__init__(parent, text="", command=command, kind="toolbar", width=theme.SQUARE,
                         height=theme.SQUARE, icon=icon)
        self.tip_text = tip
        Tooltip(self, lambda: self.tip_text)

    def set_icon(self, icon, tip=None):
        """Swaps the icon (and optionally the hover tip), for buttons like mute that change."""
        self._icon = icon
        if tip is not None:
            self.tip_text = tip
        self._show("normal" if self._enabled else "disabled")


class Tooltip:
    """A tiny hint box that shows up when the mouse rests on a widget."""

    def __init__(self, widget, text_fn, delay=450):
        """Hooks the widget's enter/leave/click events up to the hint box."""
        self.widget = widget
        self.text_fn = text_fn
        self.delay = delay
        self._after = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        """Starts the little wait before the hint appears."""
        self._hide()
        self._after = self.widget.after(self.delay, self._show)

    def _show(self):
        """Pops the hint up just under the widget."""
        self._after = None
        text = self.text_fn()
        if not text:
            return
        try:
            tip = tk.Toplevel(self.widget)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            frame = tk.Frame(tip, bg=theme.ACCENT_TEXT if theme.MODE == "light" else theme.ACCENT,
                             padx=1, pady=1)
            frame.pack()
            tk.Label(frame, text=text, bg=theme.PANEL, fg=theme.TEXT, font=theme.FONT_SMALL,
                     padx=theme.S(8), pady=theme.S(3)).pack()
            tip.update_idletasks()
            x = self.widget.winfo_rootx() + self.widget.winfo_width() - tip.winfo_reqwidth()
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + theme.S(6)
            tip.geometry(f"+{max(0, x)}+{y}")
            self._tip = tip
        except tk.TclError:
            self._tip = None

    def _hide(self, _event=None):
        """Takes the hint away."""
        if self._after is not None:
            try:
                self.widget.after_cancel(self._after)
            except tk.TclError:
                pass
            self._after = None
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None


class AuroraBar(tk.Canvas):
    """A thin colorful stripe that stretches to whatever width it's given."""

    def __init__(self, parent, height=2, accent=False):
        """Makes the stripe; with accent=True it's a plain accent-colored bar instead."""
        self._px = theme.S(height)
        super().__init__(parent, height=self._px, highlightthickness=0, bd=0,
                         bg=theme.ACCENT if accent else theme.PANEL)
        self._img = None
        self._accent = accent
        self.bind("<Configure>", self._draw)

    def _draw(self, event):
        """Paints the stripe at the new width."""
        if self._accent:
            return
        img = gfx.aurora_bar(event.width, self._px)
        if img is not None:
            self.delete("all")
            self.create_image(0, 0, image=img, anchor="nw")
            self._img = img
        else:
            self.configure(bg=theme.ACCENT)


class Panel(tk.Frame):
    """A glass-style box: a thin border, an aurora stripe along the top and gold ticks in the bottom corners.
    Put your widgets in .body."""

    def __init__(self, parent, stripe=True, ticks=True, bg=None, border=None):
        """Builds the border, stripe and corner ticks around an empty .body frame."""
        self._fill = bg or theme.PANEL
        super().__init__(parent, bg=border or theme.LINE)
        inner = tk.Frame(self, bg=self._fill)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        if stripe:
            AuroraBar(inner, 2).pack(fill="x")
        self.body = tk.Frame(inner, bg=self._fill)
        self.body.pack(fill="both", expand=True)
        if ticks:
            self._add_ticks()

    def _add_ticks(self):
        """Adds the small gold L-shaped marks in the two bottom corners."""
        length = theme.S(10)
        for relx, anchor in ((0, "sw"), (1, "se")):
            tk.Frame(self, bg=theme.TICK, width=length, height=1).place(relx=relx, rely=1, anchor=anchor)
            tk.Frame(self, bg=theme.TICK, width=1, height=length).place(relx=relx, rely=1, anchor=anchor)


class HeaderBar(tk.Canvas):
    """A colored left-to-right gradient strip with star dust and a line of text, like a team's header."""

    def __init__(self, parent, left, right, height=40, text="", font=None, fg=None, pad=16, dust=True,
                 icon=None, width=None):
        """Makes the strip; it redraws itself whenever its width changes. icon can be 'warn' or 'check'."""
        self._px = theme.S(height)
        extra = {"width": width} if width else {}
        super().__init__(parent, height=self._px, highlightthickness=0, bd=0, bg=left, **extra)
        self.icon = icon
        self.left, self.right, self.dust = left, right, dust
        self.text = text
        self.right_text = ""
        self.right_font = theme.fpx(theme.SANS, 16)
        self._font = font or theme.FONT_BODY
        self._fg = fg or theme.HEADER_INK
        self._pad = theme.S(pad)
        self._img = None
        self._right_edge = 0
        self.bind("<Configure>", self._draw)

    def set_text(self, text):
        """Changes the words on the strip."""
        self.text = text
        self._draw()

    def set_right_text(self, text, font=None):
        """Puts a second, smaller line of words at the right end of the strip (like 'Captain: Nova')."""
        self.right_text = text
        if font is not None:
            self.right_font = font
        self._draw()

    def set_colors(self, left, right):
        """Changes the two gradient colors (when the strip is reused for another team)."""
        self.left, self.right = left, right
        self.configure(bg=left)
        self._draw()

    def set_right_margin(self, pixels):
        """Reserves room on the right (for an icon or button) so the text doesn't run under it."""
        self._right_edge = pixels
        self._draw()

    def _draw(self, event=None):
        """Paints the gradient, then the text on top."""
        width = event.width if event is not None else self.winfo_width()
        if width < 2:
            return
        self.delete("all")
        img = gfx.gradient_bar(width, self._px, self.left, self.right, self.dust)
        if img is not None:
            self.create_image(0, 0, image=img, anchor="nw")
            self._img = img
        else:
            self.configure(bg=self.left)
        start = self._pad
        if self.icon:
            size = theme.S(16)
            self._draw_icon(start, (self._px - size) / 2, size)
            start += size + theme.S(12)
        room = width - start - self._pad - self._right_edge
        if self.right_text:
            side = text_width(self.right_font, self.right_text)
            side = min(side, max(0, room // 2))
            self.create_text(width - self._pad - self._right_edge, self._px // 2,
                             text=fit_text(self.right_text, self.right_font, side), anchor="e",
                             fill=self._fg, font=self.right_font)
            room -= side + theme.S(12)
        self.create_text(start, self._px // 2, text=fit_text(self.text, self._font, room),
                         anchor="w", fill=self._fg, font=self._font)

    def _draw_icon(self, x, y, s):
        """Draws the small warning triangle or check mark at the left of the strip."""
        ink = self._fg
        if self.icon == "warn":
            self.create_polygon(x + s / 2, y, x + s, y + s, x, y + s, outline=ink, fill="", width=2)
            self.create_line(x + s / 2, y + s * 0.38, x + s / 2, y + s * 0.68, fill=ink, width=2)
            self.create_line(x + s / 2, y + s * 0.8, x + s / 2, y + s * 0.84, fill=ink, width=2)
        elif self.icon == "check":
            self.create_line(x, y + s * 0.55, x + s * 0.38, y + s * 0.92, x + s, y + s * 0.1, fill=ink, width=3)


class AccentBar(tk.Canvas):
    """A bold accent-colored strip (darker at the ends) used along the top of big panels."""

    def __init__(self, parent, height=8):
        """Makes the strip; it redraws itself to its width."""
        self._px = theme.S(height)
        super().__init__(parent, height=self._px, highlightthickness=0, bd=0, bg=theme.ACCENT)
        self._img = None
        self.bind("<Configure>", self._draw)

    def _draw(self, event):
        """Paints the strip at the new width."""
        img = gfx.accent_bar(event.width, self._px)
        if img is not None:
            self.delete("all")
            self.create_image(0, 0, image=img, anchor="nw")
            self._img = img


class Chip(tk.Frame):
    """A small rectangle-shaped tag with a thin edge. accent=True gives it the accent tint; dot adds a little colored square at the left."""

    def __init__(self, parent, label, accent=False, on=None, dot=None):
        """Builds the chip at a fixed height, as wide as its text needs."""
        self._font = theme.fpx(theme.SANS, 15)
        self._accent = accent
        base = on or theme.PANEL
        fill = theme.mix(base, theme.ACCENT, 0.28) if accent else theme.mix(theme.BTN_TOP, theme.BTN_BOTTOM, 0.5)
        edge = theme.mix(base, theme.ACCENT, 0.75) if accent else theme.BTN_EDGE
        super().__init__(parent, bg=edge, height=theme.S(28))
        self._has_dot = dot is not None
        if self._has_dot:
            holder = tk.Frame(self, bg=fill)
            holder.pack(fill="both", expand=True, padx=1, pady=1)
            self._dot = tk.Frame(holder, bg=dot, width=theme.S(8), height=theme.S(8))
            self._dot.pack(side="left", padx=(theme.S(12), 0))
            self._label = tk.Label(holder, text=label, bg=fill, fg=theme.TEXT, font=self._font)
            self._label.pack(side="left", fill="both", expand=True)
        else:
            self._label = tk.Label(self, text=label, bg=fill, fg=theme.TEXT, font=self._font)
            self._label.pack(fill="both", expand=True, padx=1, pady=1)
        self.pack_propagate(False)
        self._resize(label)

    def _resize(self, label):
        """Sets the chip's width to fit the words (and the dot, if there is one)."""
        extra = theme.S(8 + 8) if self._has_dot else 0
        self.configure(width=text_width(self._font, label) + 2 * theme.S(12) + 2 + extra)

    @property
    def pixel_width(self):
        """The chip's width in real pixels (known straight away, no need to wait for the screen to draw)."""
        return int(float(self.cget("width")))

    @property
    def pixel_height(self):
        """The chip's height in real pixels."""
        return int(float(self.cget("height")))

    def set_text(self, label, dot=None):
        """Changes the chip's words (and dot color) and refits it."""
        self._label.configure(text=label)
        if dot is not None and self._has_dot:
            self._dot.configure(bg=dot)
        self._resize(label)


def style_entry(entry, bg=None):
    """Gives a text box the field look: dark/light fill with a thin edge that lights up with the accent when focused."""
    entry.configure(bg=bg or theme.PANEL_2, fg=theme.TEXT, insertbackground=theme.TEXT,
                    relief="flat", bd=0, highlightthickness=1, highlightbackground=theme.LINE,
                    highlightcolor=theme.ACCENT_TEXT, selectbackground=theme.ACCENT,
                    selectforeground=theme.ACCENT_INK, font=theme.FONT_BODY)
    return entry
