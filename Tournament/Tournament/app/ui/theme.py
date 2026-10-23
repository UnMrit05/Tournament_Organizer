"""Shared colors, fonts and sizes for the whole app: the dark and light palettes, the accent color, the grid sizes, and the scaling that makes everything fit the screen's resolution."""

# ---------- grid (reference pixels at 1280x720, scaled by S()) ----------
MARGIN = 24        # space between the window edge and the content
GUTTER = 16        # space between columns and between stacked blocks
COLUMNS = 12
HEADER_H = 40
FOOTER_H = 48
BUTTON_W = 192     # two grid columns wide - Spin/Confirm and Reset/Save/Lock Seed use this
SQUARE = 32        # toolbar buttons
SP_1, SP_2, SP_3, SP_4 = 4, 8, 16, 24

# ---------- stock accent colors ----------
STOCK_DARK = "#4FE6C4"
STOCK_LIGHT = "#E9B98D"
_PEACH_HI, _PEACH_LO, _PEACH_TEXT = "#F0CDA8", "#DCA876", "#8A4E22"

# Team colors, one flat color per team. Dark walks a cold green-to-purple ramp and light a warm pastel
# one; both alternate the two halves of their ramp so two cards side by side never look alike.
TEAM_HUES_DARK = ["#4FE8A0", "#5E9CFF", "#3FE4C0", "#8A86FF", "#3FDCDC", "#B07BF5", "#46CCF0", "#C878F0"]
TEAM_HUES_LIGHT = ["#E6A49C", "#A9BDDA", "#A7C6A6", "#C0B1DA", "#E7B0C6", "#EDBE96", "#CBD199", "#A2CAC4"]

# Filled in by _apply_palette(): the current mode's hues as (left, right) pairs, both the same color.
TEAM_HUES = [(c, c) for c in TEAM_HUES_DARK]

_PALETTES = {
    "dark": dict(
        BG="#0F1216", BG_TOP="#0F1216", BG_BOTTOM="#0F1216",
        PANEL="#161A1F", PANEL_2="#11151A", ROW="#131820", ROW_EDGE="#28303A", LINE="#333B44",
        HI="#414B55", TEXT="#E9EEF2", DIM="#A4AFB9", FAINT="#7C8792", ACTIVE_BG="#1A2228",
        BTN_TOP="#262D35", BTN_BOTTOM="#262D35", BTN_EDGE="#3B454F", BTN_INK="#E9EEF2",
        BASE="#171C21", DLG_TOP="#1C222A", DLG_BOTTOM="#1C222A", TICK="#4E8C80", HEADER_INK="#0C1412",
        AURORA=("#3E7D70", "#3E7D70", "#3E7D70", "#3E7D70"),
        VANGUARD="#5E9CFF", DUELIST="#B07BF5", STRATEGIST="#4FE8A0",
        VANGUARD_T="#93B8FF", DUELIST_T="#C9A3FF", STRATEGIST_T="#7CEFBC",
        TRACK="#1E242B",
    ),
    "light": dict(
        BG="#F2ECE1", BG_TOP="#F2ECE1", BG_BOTTOM="#F2ECE1",
        PANEL="#FAF6EE", PANEL_2="#FFFCF6", ROW="#F0E9DC", ROW_EDGE="#E5DCCC", LINE="#DCD2C1",
        HI="#FFFCF6", TEXT="#2B2620", DIM="#6C6253", FAINT="#8B8071", ACTIVE_BG="#F5EFE4",
        BTN_TOP="#F5F0E6", BTN_BOTTOM="#F5F0E6", BTN_EDGE="#D6CBB8", BTN_INK="#2B2620",
        BASE="#FAF6EE", DLG_TOP="#FFFCF6", DLG_BOTTOM="#FFFCF6", TICK="#C9A86E", HEADER_INK="#2B2620",
        AURORA=("#D3B394", "#D3B394", "#D3B394", "#D3B394"),
        VANGUARD="#7A9AC0", DUELIST="#C97961", STRATEGIST="#7FA37F",
        VANGUARD_T="#3C5F86", DUELIST_T="#8F4027", STRATEGIST_T="#40663F",
        TRACK="#E3DACB",
    ),
}

_TIER_COLORS = {
    "dark": {"Bronze": "#3FA98A", "Silver": "#46C7B4", "Gold": "#41D9D9", "Platinum": "#52B4FF",
             "Diamond": "#5E9CFF", "Grand Master": "#8A86FF", "Celestial": "#B07BF5",
             "Eternity": "#C878F0", "One Above All": "#E6DCFF"},
    "light": {"Bronze": "#C09372", "Silver": "#B3B6BC", "Gold": "#D9B46A", "Platinum": "#8CC6C4",
              "Diamond": "#93AEDA", "Grand Master": "#B49BD2", "Celestial": "#DFA2BE",
              "Eternity": "#DD9A8C", "One Above All": "#7E7A73"},
}

PLATFORM_COLOR = {"PlayStation": "#3B8FE0", "Xbox": "#3DAE3D", "PC": "#AAB2C8"}

# Colors for the current mode. These get filled in by _apply_palette() below.
BG = BG_TOP = BG_BOTTOM = PANEL = PANEL_2 = ROW = ROW_EDGE = LINE = HI = ""
TEXT = DIM = FAINT = ACTIVE_BG = BTN_TOP = BTN_BOTTOM = BTN_EDGE = BTN_INK = ""
BASE = DLG_TOP = DLG_BOTTOM = TICK = TRACK = LABEL_BG = HEADER_INK = ""
VANGUARD = DUELIST = STRATEGIST = VANGUARD_T = DUELIST_T = STRATEGIST_T = ""
AURORA = ()
GOLD = ACCENT = ACCENT_HI = ACCENT_LO = ACCENT_EDGE = ACCENT_TEXT = ACCENT_INK = ""
ROLE_COLOR = {}
ROLE_TEXT = {}
TIER_COLOR = {}

MODE = "dark"
USER_ACCENT = None          # a color picked in app_config.txt ("Theme:") or with the Theme button
_STOCK_OVERRIDE = {}        # "Theme Dark" / "Theme Light" from app_config.txt

BASE_HEIGHT = 720
SCALE = 1.0
SANS = "Segoe UI"
SEMIBOLD = "Segoe UI Semibold"
DEFAULT_SANS = SANS
DEFAULT_SEMIBOLD = SEMIBOLD
CUSTOM_FONT = None     # set via set_custom_font() / "Font:" in app_config.txt
FONT_SIZE_MULT = 1.0   # set via set_font_size_mult() / "Font Size:" in app_config.txt

# Per-screen font overrides (screen key -> family string), set via
# set_screen_fonts() / the "<Screen> Heading Font:" / "<Screen> Body Font:"
# lines in app_config.txt. "Heading" governs theme.SEMIBOLD-based text
# (titles, section headers), "Body" governs theme.SANS-based text.
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


def fpx(family, ref_px, *flags):
    """Same as font() but takes the size in reference pixels (the numbers used in the design)."""
    px = max(9, int(round(ref_px * SCALE * FONT_SIZE_MULT)))
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


# ---------- colors ----------

def _rgb(hex_color):
    """Turns '#rrggbb' into three numbers."""
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def _hex(r, g, b):
    """Turns three numbers into '#rrggbb', keeping each one in range."""
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(round(v)))) for v in (r, g, b)))


def blend(fg_hex, bg_hex, alpha):
    """Mixes one color toward another to fake see-through, since tkinter widgets can't really be transparent."""
    fg, bg = _rgb(fg_hex), _rgb(bg_hex)
    return _hex(*(f * alpha + b * (1 - alpha) for f, b in zip(fg, bg)))


def mix(a_hex, b_hex, t):
    """Moves color a toward color b by t (0 = a, 1 = b)."""
    return blend(b_hex, a_hex, t)


def _luminance(hex_color):
    """How bright a color looks (0 to 1), used to pick readable text colors."""
    chans = []
    for c in _rgb(hex_color):
        c /= 255
        chans.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def contrast(a_hex, b_hex):
    """Contrast ratio between two colors (bigger is easier to read)."""
    la, lb = _luminance(a_hex), _luminance(b_hex)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def accent_for(mode):
    """The accent color in use for a mode: a picked color wins, then the config's per-mode color, then the stock one."""
    stock = STOCK_LIGHT if mode == "light" else STOCK_DARK
    return USER_ACCENT or _STOCK_OVERRIDE.get(mode) or stock


def accent_scheme(accent, mode):
    """Works out the highlight, shadow, edge, text and ink colors that go with an accent color in a mode."""
    light = mode == "light"
    peach = light and accent.upper() == STOCK_LIGHT
    # The look is flat and matte, so the highlight and shadow sit very close to the accent itself.
    hi = _PEACH_HI if peach else mix(accent, "#FFFFFF", 0.10)
    lo = _PEACH_LO if peach else mix(accent, "#000000", 0.08)
    edge = mix(accent, "#000000", 0.30) if light else mix(accent, "#000000", 0.26)
    if peach:
        text = _PEACH_TEXT
    elif light:
        text = accent
        for _ in range(30):
            if contrast(text, "#FFFFFF") >= 5:
                break
            text = mix(text, "#000000", 0.08)
    else:
        text = accent
    ink = "#10121A" if contrast(accent, "#10121A") >= contrast(accent, "#FFFFFF") else "#FFFFFF"
    return {"hi": hi, "lo": lo, "edge": edge, "text": text, "ink": ink}


def _apply_palette():
    """Copies the current mode's colors and the accent colors into the module-level names the screens read."""
    g = globals()
    pal = _PALETTES[MODE]
    for key, value in pal.items():
        g[key] = value
    hues = TEAM_HUES_LIGHT if MODE == "light" else TEAM_HUES_DARK
    g["TEAM_HUES"] = [(c, c) for c in hues]
    accent = accent_for(MODE)
    scheme = accent_scheme(accent, MODE)
    g["GOLD"] = accent
    g["ACCENT"] = accent
    g["ACCENT_HI"] = scheme["hi"]
    g["ACCENT_LO"] = scheme["lo"]
    g["ACCENT_EDGE"] = scheme["edge"]
    g["ACCENT_TEXT"] = scheme["text"]
    g["ACCENT_INK"] = scheme["ink"]
    g["ROLE_COLOR"] = {"Vanguard": pal["VANGUARD"], "Duelist": pal["DUELIST"], "Strategist": pal["STRATEGIST"]}
    g["ROLE_TEXT"] = {"Vanguard": pal["VANGUARD_T"], "Duelist": pal["DUELIST_T"], "Strategist": pal["STRATEGIST_T"]}
    g["TIER_COLOR"] = _TIER_COLORS[MODE]
    g["LABEL_BG"] = pal["PANEL"]


def set_mode(mode):
    """Switches between the 'dark' and 'light' palettes."""
    global MODE
    MODE = "light" if mode == "light" else "dark"
    _apply_palette()


def set_accent(hex_color):
    """Changes the accent color (used in both modes) everywhere in the app."""
    global USER_ACCENT
    if hex_color:
        USER_ACCENT = hex_color
        _apply_palette()


def set_stock_accents(dark=None, light=None):
    """Remembers the per-mode starting accents from app_config.txt ('Theme Dark' / 'Theme Light')."""
    global _STOCK_OVERRIDE
    _STOCK_OVERRIDE = {}
    if dark:
        _STOCK_OVERRIDE["dark"] = dark
    if light:
        _STOCK_OVERRIDE["light"] = light
    _apply_palette()


def color_for(mode, key):
    """One palette color for a mode that may not be the one on screen (used when drawing ahead of time)."""
    return _PALETTES.get(mode, _PALETTES["dark"]).get(key, BG)


def team_hue(index):
    """Gives back the (left, right) colors for the team at this position, cycling through the list."""
    return TEAM_HUES[index % len(TEAM_HUES)]


def row_colors(card_bg):
    """The fill and edge colors for a row sitting on a card of this color."""
    if MODE == "dark":
        return mix(card_bg, "#000000", 0.26), mix(card_bg, "#FFFFFF", 0.09)
    return mix(card_bg, PANEL_2, 0.72), mix(card_bg, "#2B2620", 0.12)


def team_body_color(hue_pair):
    """The tinted card color for a team: a hint of its first color over the card base."""
    return mix(BASE, hue_pair[0], 0.14 if MODE == "dark" else 0.10)


# ---------- fonts ----------

def _rebuild_fonts():
    """Re-makes the ready-made font sets (title, heading, body, small, and so on) after a font or size change."""
    global FONT_DISPLAY, FONT_HEADING, FONT_NAME, FONT_BODY, FONT_SMALL
    global FONT_TITLE, FONT_BUTTON, FONT_SECTION, FONT_NOTE, FONT_STEP
    FONT_DISPLAY = font(SEMIBOLD, 26)
    FONT_HEADING = font(SEMIBOLD, 18)
    FONT_NAME = fpx(SANS, 18)
    FONT_BODY = fpx(SANS, 18)
    FONT_SMALL = fpx(SANS, 14)
    FONT_NOTE = fpx(SANS, 16)
    FONT_TITLE = fpx(SEMIBOLD, 28)
    FONT_BUTTON = fpx(SEMIBOLD, 14)
    FONT_SECTION = fpx(SEMIBOLD, 12)
    FONT_STEP = fpx(SEMIBOLD, 11)


set_mode("dark")
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


def apply_ttk_style(root):
    """Themes the dropdowns and scrollbars so they match the current palette."""
    import tkinter as tk
    from tkinter import ttk

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TCombobox", fieldbackground=PANEL_2, background=ROW, foreground=TEXT,
                     arrowcolor=TEXT, bordercolor=LINE, lightcolor=PANEL_2, darkcolor=PANEL_2,
                     arrowsize=S(14), padding=S(3))
    style.map("TCombobox",
              fieldbackground=[("readonly", PANEL_2), ("disabled", PANEL)],
              foreground=[("readonly", TEXT), ("disabled", DIM)],
              arrowcolor=[("disabled", DIM)])
    root.option_add("*TCombobox*Listbox.font", FONT_SMALL)
    root.option_add("*TCombobox*Listbox.background", PANEL_2)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", ACCENT_INK)

    for orient in ("Vertical", "Horizontal"):
        style.configure(f"Glass.{orient}.TScrollbar", background=FAINT, troughcolor=TRACK,
                         bordercolor=TRACK, lightcolor=FAINT, darkcolor=FAINT, arrowcolor=TEXT,
                         arrowsize=S(10), gripcount=0, relief="flat")
        style.map(f"Glass.{orient}.TScrollbar", background=[("active", DIM), ("pressed", ACCENT)])
