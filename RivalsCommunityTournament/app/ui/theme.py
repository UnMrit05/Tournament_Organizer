"""Shared visual theme constants and resolution-aware UI scaling.

The layout was designed at a 720px-tall baseline. init_scale() picks a
scale from the screen height (1440p -> ~1.9x, 1080p -> ~1.4x) so a
maximized window is filled instead of leaving the UI tiny. Pixel sizes
go through S(); fonts go through font(), which uses pixel sizes so
Windows DPI settings can't double-scale it.

Screens read theme.FONT_* / call theme.S()/theme.button_kwargs() at
render time (not import time), so as long as init_scale() runs before
the first screen is built, every screen picks up the scaled values
automatically with no per-screen changes needed.
"""

BG = "#0E0F13"
PANEL = "#191B22"
PANEL_2 = "#23262F"
LINE = "#333749"
TEXT = "#ECEEF3"
DIM = "#8B90A3"

VANGUARD = "#4C8DFF"
DUELIST = "#FF6B57"
STRATEGIST = "#33D6A6"
GOLD = "#E8B854"
ACTIVE_BG = "#1E2130"
PLATFORM_COLOR = {"PlayStation": "#3B8FE0", "Xbox": "#3DAE3D", "PC": "#AAB2C8"}

ROLE_COLOR = {"Vanguard": VANGUARD, "Duelist": DUELIST, "Strategist": STRATEGIST}

BASE_HEIGHT = 720
SCALE = 1.0
SANS = "Segoe UI"
SEMIBOLD = "Segoe UI Semibold"
DEFAULT_SANS = SANS
DEFAULT_SEMIBOLD = SEMIBOLD
CUSTOM_FONT = None     # set via set_custom_font() / "Font:" in tournament_info.txt
DEFAULT_ACCENT = GOLD


def S(value):
    """Scale a pixel value by the current UI scale."""
    if not value:
        return 0
    return max(1, int(round(value * SCALE)))


def font(family, size_pt, *flags):
    """A Tk font tuple in negative (pixel) size, scaled by SCALE, so
    Windows text-scaling settings don't compound with ours. When a custom
    font is active it replaces both the body and "semibold" family - most
    user fonts don't ship a dedicated semibold face, so a bold flag is
    substituted automatically wherever the semibold face was asked for."""
    px = max(9, int(round(size_pt * 96 / 72 * SCALE)))
    fam = family
    if CUSTOM_FONT:
        fam = CUSTOM_FONT
        if family == DEFAULT_SEMIBOLD and "bold" not in flags:
            flags = tuple(flags) + ("bold",)
    return (fam, -px) + tuple(flags)


def set_custom_font(name):
    """Switch the app's font family (None/"" restores the default). Callers
    should rebuild the current screen afterward so already-built widgets
    pick up the new font."""
    global CUSTOM_FONT, SANS, SEMIBOLD
    CUSTOM_FONT = (name or "").strip() or None
    SANS = CUSTOM_FONT or DEFAULT_SANS
    SEMIBOLD = CUSTOM_FONT or DEFAULT_SEMIBOLD
    _rebuild_fonts()


def set_accent(hex_color):
    """Replace the gold accent color app-wide. Callers should rebuild the
    current screen (and re-run apply_ttk_style) afterward so already-built
    widgets pick up the new color."""
    global GOLD
    if hex_color:
        GOLD = hex_color


def _rebuild_fonts():
    global FONT_DISPLAY, FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_NAME
    FONT_DISPLAY = font(SEMIBOLD, 26)
    FONT_HEADING = font(SEMIBOLD, 18)
    FONT_NAME = font(SEMIBOLD, 11)
    FONT_BODY = font(SANS, 11)
    FONT_SMALL = font(SANS, 9)


_rebuild_fonts()


def init_scale(root, override=None):
    global SCALE
    if override:
        SCALE = max(0.6, min(4.0, float(override)))
    else:
        SCALE = max(1.0, min(3.0, (root.winfo_screenheight() - 60) / BASE_HEIGHT))
    _rebuild_fonts()
    return SCALE


def primary_button_kwargs():
    return dict(bg=GOLD, fg="#181205", activebackground=GOLD, relief="flat",
                padx=S(18), pady=S(8), font=FONT_BODY, bd=0, cursor="hand2")


def button_kwargs():
    return dict(bg=PANEL_2, fg=TEXT, activebackground=LINE, relief="flat",
                padx=S(18), pady=S(8), font=FONT_BODY, bd=0, cursor="hand2")


def apply_ttk_style(root):
    """Dark-theme the ttk widgets we use: Combobox (+ its dropdown list)
    and scrollbars."""
    import tkinter as tk
    from tkinter import ttk

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TCombobox", fieldbackground=PANEL_2, background=PANEL_2, foreground=TEXT,
                     arrowcolor=TEXT, bordercolor=LINE, lightcolor=PANEL_2, darkcolor=PANEL_2,
                     arrowsize=S(14), padding=S(3))
    style.map("TCombobox",
              fieldbackground=[("readonly", PANEL_2), ("disabled", PANEL)],
              foreground=[("readonly", TEXT), ("disabled", DIM)],
              arrowcolor=[("disabled", DIM)])
    root.option_add("*TCombobox*Listbox.font", FONT_SMALL)
    root.option_add("*TCombobox*Listbox.background", PANEL_2)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", GOLD)
    root.option_add("*TCombobox*Listbox.selectForeground", "#181205")

    for orient in ("Vertical", "Horizontal"):
        style.configure(f"Glass.{orient}.TScrollbar", background=LINE, troughcolor="",
                         bordercolor=BG, lightcolor=LINE, darkcolor=LINE, arrowcolor=TEXT,
                         arrowsize=S(14), gripcount=0, relief="flat")
        style.map(f"Glass.{orient}.TScrollbar", background=[("active", DIM), ("pressed", GOLD)])
