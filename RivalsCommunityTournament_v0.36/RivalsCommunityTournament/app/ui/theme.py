"""Shared colors, fonts and sizes for the whole app, plus the scaling that makes everything fit the screen's resolution."""

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
CUSTOM_FONT = None     # set via set_custom_font() / "Font:" in app_config.txt
DEFAULT_ACCENT = GOLD
FONT_SIZE_MULT = 1.0   # set via set_font_size_mult() / "Font Size:" in app_config.txt

# Per-screen font overrides (screen key -> family string), set via
# set_screen_fonts() / the "<Screen> Heading Font:" / "<Screen> Body Font:"
# lines in app_config.txt. "Heading" governs theme.SEMIBOLD-based text
# (titles, section headers - this is also where the Greeting/Congrats screen
# headings are controlled), "Body" governs theme.SANS-based text.
SCREEN_HEADING_FONT = {}
SCREEN_BODY_FONT = {}


def S(value):
    """Scales a pixel size to fit this screen's resolution."""
    if not value:
        return 0
    return max(1, int(round(value * SCALE)))


def font(family, size_pt, *flags):
    """Builds a tkinter font tuple at the right size for this screen (and swaps in bold when a custom font has no semibold)."""
    px = max(9, int(round(size_pt * 96 / 72 * SCALE * FONT_SIZE_MULT)))
    flags = tuple(flags)
    if family == SEMIBOLD and SEMIBOLD != DEFAULT_SEMIBOLD and "bold" not in flags:
        flags = flags + ("bold",)
    return (family, -px) + flags


def set_custom_font(name):
    """Switches the app-wide font family (an empty name goes back to the default)."""
    global CUSTOM_FONT, SANS, SEMIBOLD
    CUSTOM_FONT = (name or "").strip() or None
    SANS = CUSTOM_FONT or DEFAULT_SANS
    SEMIBOLD = CUSTOM_FONT or DEFAULT_SEMIBOLD
    _rebuild_fonts()


def set_font_size_mult(mult):
    """Makes every font bigger or smaller by this multiplier."""
    global FONT_SIZE_MULT
    try:
        FONT_SIZE_MULT = max(0.5, min(3.0, float(mult)))
    except (TypeError, ValueError):
        FONT_SIZE_MULT = 1.0
    _rebuild_fonts()


def set_screen_fonts(heading_map, body_map):
    """Remembers which screens have their own heading/body fonts from the config file."""
    global SCREEN_HEADING_FONT, SCREEN_BODY_FONT
    SCREEN_HEADING_FONT = dict(heading_map or {})
    SCREEN_BODY_FONT = dict(body_map or {})


def set_active_screen(screen_name):
    """Points the fonts at whatever the given screen should use. Call before building that screen."""
    global SANS, SEMIBOLD
    SEMIBOLD = SCREEN_HEADING_FONT.get(screen_name) or CUSTOM_FONT or DEFAULT_SEMIBOLD
    SANS = SCREEN_BODY_FONT.get(screen_name) or CUSTOM_FONT or DEFAULT_SANS
    _rebuild_fonts()


def set_accent(hex_color):
    """Changes the accent color (the gold) used all over the app."""
    global GOLD
    if hex_color:
        GOLD = hex_color


def blend(fg_hex, bg_hex, alpha):
    """Mixes one color toward another to fake see-through, since tkinter widgets can't really be transparent."""
    fg = tuple(int(fg_hex[i:i + 2], 16) for i in (1, 3, 5))
    bg = tuple(int(bg_hex[i:i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(round(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def _rebuild_fonts():
    """Re-makes the ready-made font sets (heading, body, small, and so on) after a font or size change."""
    global FONT_DISPLAY, FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_NAME
    FONT_DISPLAY = font(SEMIBOLD, 26)
    FONT_HEADING = font(SEMIBOLD, 18)
    FONT_NAME = font(SEMIBOLD, 11)
    FONT_BODY = font(SANS, 11)
    FONT_SMALL = font(SANS, 9)


_rebuild_fonts()


def init_scale(root, override=None):
    """Works out how much to scale everything from the screen height (or uses the Scale: override from the config)."""
    global SCALE
    if override:
        SCALE = max(0.6, min(4.0, float(override)))
    else:
        SCALE = max(1.0, min(3.0, (root.winfo_screenheight() - 60) / BASE_HEIGHT))
    _rebuild_fonts()
    return SCALE


def primary_button_kwargs():
    """Settings for the big accent-colored main buttons."""
    return dict(bg=GOLD, fg="#181205", activebackground=GOLD, relief="flat",
                padx=S(18), pady=S(8), font=FONT_BODY, bd=0, cursor="hand2")


def button_kwargs():
    """Settings for the normal dark buttons."""
    return dict(bg=PANEL_2, fg=TEXT, activebackground=LINE, relief="flat",
                padx=S(18), pady=S(8), font=FONT_BODY, bd=0, cursor="hand2")


def apply_ttk_style(root):
    """Dark-themes the dropdowns and scrollbars so they match the rest of the app."""
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
