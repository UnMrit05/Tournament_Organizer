"""The accent color picker window: R/G/B sliders, a hex box, preset swatches and a live preview."""

import tkinter as tk

from app.ui import gfx, text, theme
from app.ui.widgets import AuroraBar, Chip, GlassButton, style_entry

PRESETS = ["#4FE6C4", "#E9B98D", "#4FE8A0", "#5E9CFF", "#B07BF5", "#C878F0", "#A9BDDA", "#C97961"]


def _hex_ok(value):
    """Says whether the text is a proper #rrggbb color."""
    value = value.strip().lstrip("#")
    return len(value) == 6 and all(c in "0123456789abcdefABCDEF" for c in value)


class ChannelSlider(tk.Canvas):
    """A slider for one color channel (0-255) with a gradient track and a square handle."""

    def __init__(self, parent, on_change, bg):
        """Builds the track and hooks up dragging."""
        self._track_h = theme.S(8)
        self._thumb_w = theme.S(10)
        super().__init__(parent, height=theme.S(24), highlightthickness=0, bd=0, bg=bg)
        self._bg = bg
        self.value = 0
        self._colors = ("#000000", "#FFFFFF")
        self._on_change = on_change
        self._img = None
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._drag)
        self.bind("<B1-Motion>", self._drag)

    def set(self, value, colors=None):
        """Sets the handle position (and optionally the two colors the track fades between)."""
        self.value = max(0, min(255, int(value)))
        if colors:
            self._colors = colors
        self._draw()

    def _drag(self, event):
        """Moves the handle to the mouse and tells the picker."""
        width = max(1, self.winfo_width() - self._thumb_w)
        value = int(round((event.x - self._thumb_w / 2) / width * 255))
        self.set(value)
        self._on_change(self.value)

    def _draw(self):
        """Paints the track and the handle."""
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        self.delete("all")
        top = (h - self._track_h) // 2
        img = gfx.channel_track(w, self._track_h, *self._colors)
        if img is not None:
            self._img = img
            self.create_image(0, top, image=img, anchor="nw")
        else:
            self.create_rectangle(0, top, w, top + self._track_h, fill=self._colors[1], outline="")
        self.create_rectangle(0, top, w - 1, top + self._track_h - 1, outline=theme.LINE)
        x = self._thumb_w / 2 + (w - self._thumb_w) * self.value / 255
        self.create_rectangle(x - self._thumb_w / 2 - 2, 1, x + self._thumb_w / 2 + 2, h - 1,
                              fill=theme.BASE, outline="")
        self.create_rectangle(x - self._thumb_w / 2, 3, x + self._thumb_w / 2, h - 3, fill=theme.TEXT, outline="")


def open_accent_picker(app, parent):
    """Opens the accent color window. Apply sends the chosen color to the app; Cancel just closes it."""
    try:
        start = theme.ACCENT
        r0, g0, b0 = int(start[1:3], 16), int(start[3:5], 16), int(start[5:7], 16)
    except (ValueError, IndexError):
        r0, g0, b0 = 255, 210, 31

    top = tk.Toplevel(parent)
    top.title("Accent Color")
    top.configure(bg=theme.BG)
    top.transient(parent.winfo_toplevel())
    top.resizable(False, False)

    body = tk.Frame(top, bg=theme.BG)
    body.pack(padx=theme.S(24), pady=theme.S(24))
    state = {"r": r0, "g": g0, "b": b0, "syncing": False}

    head = tk.Frame(body, bg=theme.BG)
    head.pack(fill="x")
    tk.Label(head, text="ACCENT COLOR", bg=theme.BG, fg=theme.TEXT, font=theme.fpx(theme.SEMIBOLD, 22)).pack(side="left")
    tk.Label(head, text="RGB or hex", bg=theme.BG, fg=theme.DIM, font=theme.FONT_NOTE).pack(
        side="left", padx=(theme.S(12), 0), pady=(theme.S(4), 0))

    mid = tk.Frame(body, bg=theme.BG)
    mid.pack(fill="x", pady=(theme.S(16), 0))
    swatch = tk.Label(mid, bd=0, anchor="sw", padx=theme.S(12), pady=theme.S(10),
                      font=theme.fpx(theme.SEMIBOLD, 13), compound="center")
    swatch.pack(side="left")
    channels = tk.Frame(mid, bg=theme.BG)
    channels.pack(side="left", fill="both", expand=True, padx=(theme.S(24), 0))

    sliders, boxes = {}, {}
    variables = {k: tk.StringVar(value=str(state[k])) for k in "rgb"}
    hex_var = tk.StringVar()

    def current_hex():
        """The chosen color as '#rrggbb'."""
        return "#{:02x}{:02x}{:02x}".format(state["r"], state["g"], state["b"])

    def refresh(skip=None):
        """Updates the swatch, sliders, number boxes, hex box and preview to match the chosen color."""
        state["syncing"] = True
        hex_value = current_hex()
        scheme = theme.accent_scheme(hex_value, theme.MODE)
        img = gfx.vertical_swatch(theme.S(120), theme.S(128), [(0, scheme["hi"]), (0.52, hex_value), (1, scheme["lo"])])
        swatch.configure(image=img or "", text=hex_value.upper(), fg=scheme["ink"],
                         bg=hex_value, width=theme.S(120) if img else 12, height=theme.S(128) if img else 6)
        swatch._img = img
        for key, idx in (("r", 0), ("g", 1), ("b", 2)):
            others = [state["r"], state["g"], state["b"]]
            low, high = list(others), list(others)
            low[idx], high[idx] = 0, 255
            sliders[key].set(state[key], ("#{:02x}{:02x}{:02x}".format(*low), "#{:02x}{:02x}{:02x}".format(*high)))
            if skip != key:
                variables[key].set(str(state[key]))
        if skip != "hex":
            hex_var.set(hex_value)
        preview_chip.configure(bg=theme.mix(theme.PANEL, hex_value, 0.75))
        preview_chip._label.configure(bg=theme.mix(theme.PANEL, hex_value, 0.28))
        preview_node.configure(bg=hex_value, fg=scheme["ink"])
        btn_img = gfx.vertical_swatch(theme.S(96), theme.S(32), [
            (0, scheme["hi"]), (0.52, hex_value), (1, scheme["lo"])])
        preview_btn.configure(image=btn_img or "", fg=scheme["ink"], bg=hex_value)
        preview_btn._img = btn_img
        for chip_btn, color in preset_buttons:
            chip_btn.configure(highlightbackground=theme.TEXT if color.lower() == hex_value.lower() else theme.LINE,
                               highlightthickness=2 if color.lower() == hex_value.lower() else 1)
        state["syncing"] = False

    def set_channel(key, value):
        """Changes one of R/G/B and repaints everything."""
        state[key] = max(0, min(255, int(value)))
        refresh()

    for key, label in (("r", "R"), ("g", "G"), ("b", "B")):
        row = tk.Frame(channels, bg=theme.BG)
        row.pack(fill="x", pady=theme.S(2))
        tk.Label(row, text=label, bg=theme.BG, fg=theme.DIM, font=theme.fpx(theme.SEMIBOLD, 12),
                 width=2, anchor="w").pack(side="left")
        slider = ChannelSlider(row, lambda v, k=key: set_channel(k, v), theme.BG)
        slider.pack(side="left", fill="x", expand=True, padx=(0, theme.S(12)))
        sliders[key] = slider
        box = tk.Entry(row, textvariable=variables[key], width=4, justify="right")
        style_entry(box)
        box.pack(side="left", ipady=theme.S(4))
        boxes[key] = box

        def on_type(*_a, k=key):
            """Reads the number typed in a box (0-255) and applies it."""
            if state["syncing"]:
                return
            raw = variables[k].get().strip()
            if raw.isdigit():
                state[k] = max(0, min(255, int(raw)))
                refresh(skip=k)
        variables[key].trace_add("write", on_type)

    hex_row = tk.Frame(channels, bg=theme.BG)
    hex_row.pack(fill="x", pady=theme.S(2))
    tk.Label(hex_row, text="HEX", bg=theme.BG, fg=theme.DIM, font=theme.fpx(theme.SEMIBOLD, 12)).pack(side="left")
    hex_entry = tk.Entry(hex_row, textvariable=hex_var, width=9)
    style_entry(hex_entry)
    hex_entry.pack(side="left", padx=(theme.S(12), 0), ipady=theme.S(4))

    def on_hex(*_a):
        """Applies a typed 6-digit hex code."""
        if state["syncing"]:
            return
        value = hex_var.get().strip()
        if not value.startswith("#"):
            value = "#" + value
        if _hex_ok(value):
            state["r"], state["g"], state["b"] = int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)
            refresh(skip="hex")
    hex_var.trace_add("write", on_hex)

    preset_row = tk.Frame(body, bg=theme.BG)
    preset_row.pack(fill="x", pady=(theme.S(16), 0))
    preset_buttons = []
    blank = tk.PhotoImage(width=1, height=1)
    for color in PRESETS:
        btn = tk.Button(preset_row, bg=color, activebackground=color, bd=0, relief="flat", cursor="hand2",
                        highlightthickness=1, highlightbackground=theme.LINE, takefocus=0,
                        image=blank, width=theme.S(36), height=theme.S(36))
        btn._blank = blank
        btn.pack(side="left", padx=(0, theme.S(8)))
        btn.configure(command=lambda c=color: (state.update(r=int(c[1:3], 16), g=int(c[3:5], 16), b=int(c[5:7], 16)), refresh()))
        preset_buttons.append((btn, color))

    preview = tk.Frame(body, bg=theme.LINE)
    preview.pack(fill="x", pady=(theme.S(16), 0))
    inner = tk.Frame(preview, bg=theme.PANEL)
    inner.pack(fill="x", padx=1, pady=1)
    AuroraBar(inner, 2).pack(fill="x")
    row = tk.Frame(inner, bg=theme.PANEL)
    row.pack(fill="x", padx=theme.S(16), pady=theme.S(12))
    tk.Label(row, text="PREVIEW", bg=theme.PANEL, fg=theme.DIM, font=theme.fpx(theme.SEMIBOLD, 11)).pack(side="left")
    preview_btn = tk.Label(row, text="START", font=theme.FONT_BUTTON, compound="center", bd=0)
    preview_btn.pack(side="right")
    preview_chip = Chip(row, "Lock Seed", accent=True)
    preview_chip.pack(side="right", padx=theme.S(16))
    preview_node = tk.Label(row, text="3", font=theme.FONT_STEP, width=2, height=1)
    preview_node.pack(side="right")

    actions = tk.Frame(body, bg=theme.BG)
    actions.pack(fill="x", pady=(theme.S(24), 0))

    def apply():
        """Sends the chosen color to the app and closes the window."""
        app.set_accent(current_hex())
        top.destroy()

    GlassButton(actions, text.t("Button Apply"), apply, kind="primary").pack(side="right")
    GlassButton(actions, text.t("Button Cancel"), top.destroy, kind="secondary").pack(side="right", padx=(0, theme.S(16)))

    top.update_idletasks()
    refresh()
    x = parent.winfo_toplevel().winfo_rootx() + (parent.winfo_toplevel().winfo_width() - top.winfo_reqwidth()) // 2
    y = parent.winfo_toplevel().winfo_rooty() + (parent.winfo_toplevel().winfo_height() - top.winfo_reqheight()) // 2
    top.geometry(f"+{max(0, x)}+{max(0, y)}")
    top.bind("<Escape>", lambda e: top.destroy())
    top.grab_set()
