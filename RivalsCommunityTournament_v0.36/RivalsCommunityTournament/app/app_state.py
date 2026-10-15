"""The main window. Holds the shared tournament state, the top-right toolbar,
the watermark, and switches between screens."""

import re
import sys
import tkinter as tk
from pathlib import Path

from app.data.icons import ICON_FILENAMES as ROLE_ICON_FILENAMES
from app.data.platforms import ICON_FILENAMES as PLATFORM_ICON_FILENAMES
from app.data.players import load_players
from app.data.ranks import rank_sort_key
from app.data.roster import load_roster
from app.data.team import Team
from app.ui import audio, theme

BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
ICONS_DIR = ASSETS_DIR / "icons"

PLAYERS_CSV = DATA_DIR / "players.csv"
ROSTER_JSON = DATA_DIR / "characters.json"
CONFIG_TXT = ASSETS_DIR / "app_config.txt"

APP_VERSION = "0.36"
LICENSE_NAME = "MIT License"

# Windows groups taskbar buttons by this id. Giving the app its own means it
# gets its own icon instead of sharing Python's.
_APP_USER_MODEL_ID = "RivalsCommunityTournament.App"

_MUTE_ICON = "\U0001F507"      # muted speaker
_UNMUTE_ICON = "\U0001F50A"    # speaker, high volume
_FULLSCREEN_ICON = "⛶"
_EXIT_FULLSCREEN_ICON = "✕"

# Label used in app_config.txt -> the screen name the app uses internally.
# Only needed for the per-screen "<Label> Heading Font:" / "<Label> Body Font:" lines.
_SCREEN_FONT_LABELS = [
    ("Greeting", "greeting"),
    ("Drafting", "seeding"),
    ("Tournament Type", "tournament_type"),
    ("Mystery Hero", "mystery_spin"),
    ("Bracket Settings", "bracket_settings"),
    ("Bracket", "bracket"),
    ("Congratulations", "congrats"),
    ("Congrats", "congrats"),
]

# Where the little "Made by Mrit" watermark sits. Screens not listed here get bottom-right.
_WATERMARK_BOTTOM_CENTER = {"bracket", "mystery_spin"}
_WATERMARK_BOTTOM_LEFT = {"seeding", "bracket_settings"}

# Names the "Theme:" line in app_config.txt can go by.
_THEME_KEYS = ("theme", "default theme", "theme color", "theme colour",
               "accent", "accent color", "accent colour")

_CONFIG_LINE = re.compile(r"^([^:=#]+?)\s*[:=]\s*(.*)$")


def _config_lines():
    """Reads app_config.txt and gives back its lines. Copes with the odd ways
    Notepad can save a file (with a BOM, or as UTF-16) so nothing silently breaks."""
    if not CONFIG_TXT.exists():
        return []
    try:
        raw = CONFIG_TXT.read_bytes()
    except OSError:
        return []
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16", errors="replace")
    else:
        text = raw.decode("utf-8-sig", errors="replace")
    return [ln.strip() for ln in text.splitlines()]


def read_config_value(*keys):
    """Finds the first line in app_config.txt that looks like 'Key: value' (or
    'Key = value') for any of the given key names, ignoring upper/lower case,
    extra spaces and commented-out lines. Gives back the value, or None."""
    wanted = {k.lower() for k in keys}
    for line in _config_lines():
        if not line or line.startswith("#"):
            continue
        m = _CONFIG_LINE.match(line)
        if m and m.group(1).strip().lower() in wanted:
            value = m.group(2).strip().strip("\"'").strip()
            return value or None
    return None


def _to_float(value):
    """Turns text like '1.5' (or '6 - nice and loud') into a number, or None if it isn't one."""
    if value is None:
        return None
    try:
        return float(value.split()[0])
    except (ValueError, IndexError):
        return None


def _set_windows_app_id():
    """On Windows, gives the app its own taskbar identity so the taskbar shows
    our icon rather than Python's. Does nothing anywhere else."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_APP_USER_MODEL_ID)
    except Exception:
        pass


def _find_app_icon():
    """Looks in assets/icons for the app's icon. Uses app.ico if it's there,
    otherwise any other .ico that isn't one of the built-in role/platform icons."""
    preferred = ICONS_DIR / "app.ico"
    if preferred.exists():
        return preferred
    if not ICONS_DIR.exists():
        return None
    builtin = {n.lower() for n in ROLE_ICON_FILENAMES.values()}
    builtin |= {n.lower() for n in PLATFORM_ICON_FILENAMES.values()}
    for path in sorted(ICONS_DIR.iterdir()):
        if path.suffix.lower() == ".ico" and path.name.lower() not in builtin:
            return path
    return None


class TournamentApp(tk.Tk):
    """The whole app window. Screens read and write the tournament info stored on it."""

    def __init__(self):
        """Sets up the window, reads app_config.txt, builds the toolbar and
        watermark, loads the data, and shows the Greeting screen."""
        _set_windows_app_id()
        super().__init__()
        self.title(f"Rivals Community Tournament v{APP_VERSION}")
        self.configure(bg=theme.BG)

        theme.init_scale(self, self._read_info_override("scale"))
        font_override = self._read_info_override("font", as_float=False)
        if font_override:
            theme.set_custom_font(font_override)
        font_size_override = self._read_info_override("font size", as_float=True)
        if font_size_override:
            theme.set_font_size_mult(font_size_override)
        heading_fonts, body_fonts = self._read_screen_fonts()
        theme.set_screen_fonts(heading_fonts, body_fonts)

        # Optional starting accent color from the config file.
        theme_color = self._normalize_color(read_config_value(*_THEME_KEYS))
        if theme_color:
            theme.set_accent(theme_color)

        # Optional starting music volume (1-10), set before any music plays.
        volume_override = self._read_info_override("volume", as_float=True)
        if volume_override is not None:
            audio.set_default_volume(volume_override)

        theme.apply_ttk_style(self)

        self.geometry(f"{theme.S(1100)}x{theme.S(720)}")
        self.minsize(theme.S(860), theme.S(600))
        try:
            self.state("zoomed")  # fill the screen by default (Windows)
        except tk.TclError:
            pass
        self._apply_app_icon()

        # Stuff the screens share with each other.
        self.players = []          # list[app.data.players.Player]
        self.roster = []           # list[app.data.roster.Character]
        self.teams = []            # filled in during Drafting
        self.tournament_type = None    # "mystery" | "normal"
        self.bracket_type = None       # "single" | "double" | "league"
        self.bracket = None
        self.bracket_order = None      # teams in seed order (Bracket Settings)
        self.bracket_settings_origin = None   # "mystery_spin" | "tournament_type"

        self._container = tk.Frame(self, bg=theme.BG)
        self._container.pack(fill="both", expand=True)
        self._current_screen = None
        self._current_screen_name = None

        self._build_toolbar()
        self._build_watermark()

        # One click sound for every tk.Button in the app, without touching
        # each button: bind_class covers all of them, and add="+" keeps each
        # button's own command working.
        self.bind_class("Button", "<Button-1>", audio.play_click, add="+")

        self._load_data()
        self.show_screen("greeting")

    def _read_info_override(self, key, as_float=True):
        """Reads one setting from app_config.txt. Gives back a number (or None if
        it isn't one) when as_float is True, otherwise the raw text (or None)."""
        value = read_config_value(key)
        return _to_float(value) if as_float else value

    def _normalize_color(self, value):
        """Turns a color from the config file ('#3FA7FF', '3fa7ff', '#fff' or a name
        like 'blue') into a plain '#rrggbb' string. Gives back None if it isn't a real color."""
        if not value:
            return None
        text = value.split()[0].strip("\"'")
        if re.fullmatch(r"[0-9a-fA-F]{6}|[0-9a-fA-F]{3}", text):
            text = "#" + text
        try:
            r, g, b = self.winfo_rgb(text)
        except tk.TclError:
            return None
        return "#{:02x}{:02x}{:02x}".format(r >> 8, g >> 8, b >> 8)

    def _read_screen_fonts(self):
        """Reads the optional per-screen font lines (like 'Bracket Heading Font: Impact')
        from app_config.txt. Gives back two dicts (heading fonts, body fonts) keyed by
        screen name."""
        heading_map, body_map = {}, {}
        for label, key in _SCREEN_FONT_LABELS:
            heading = read_config_value(f"{label} Heading Font")
            if heading:
                heading_map[key] = heading
            body = read_config_value(f"{label} Body Font")
            if body:
                body_map[key] = body
        return heading_map, body_map

    # ---------- top-right toolbar: Mute, Vol down, Vol up, Fullscreen ----------

    def _build_toolbar(self):
        """Builds the four little buttons in the top-right corner (mute, volume down,
        volume up, fullscreen). They live on the main window, not on a screen, so
        they stay put when you switch screens. Each one is an exact pixel square."""
        self._fullscreen = False
        self.bind("<Escape>", self._exit_fullscreen)

        # A blank 1x1 image on each button makes tkinter measure width/height in
        # real pixels (instead of "characters"/"lines"), which is what lets us make
        # them truly square no matter which symbol is on them.
        self._toolbar_px = tk.PhotoImage(width=1, height=1)
        size = theme.S(24)
        btn_kwargs = dict(image=self._toolbar_px, compound="center", width=size, height=size,
                           bg=theme.PANEL_2, fg=theme.GOLD, activebackground=theme.LINE,
                           activeforeground=theme.GOLD, relief="flat", bd=0, highlightthickness=0,
                           takefocus=0, cursor="hand2", padx=0, pady=0,
                           font=theme.font(theme.SANS, 9))

        toolbar = tk.Frame(self, bg=theme.BG)
        toolbar.place(relx=1.0, x=-theme.S(8), y=theme.S(4), anchor="ne")

        self._mute_btn = tk.Button(toolbar, text=_UNMUTE_ICON, command=self._toggle_mute, **btn_kwargs)
        self._mute_btn.pack(side="left", padx=(0, theme.S(4)))
        voldown_btn = tk.Button(toolbar, text="−", command=lambda: self._nudge_volume(-0.1), **btn_kwargs)
        voldown_btn.pack(side="left", padx=(0, theme.S(4)))
        volup_btn = tk.Button(toolbar, text="+", command=lambda: self._nudge_volume(0.1), **btn_kwargs)
        volup_btn.pack(side="left", padx=(0, theme.S(4)))
        self._fs_btn = tk.Button(toolbar, text=_FULLSCREEN_ICON, command=self._toggle_fullscreen, **btn_kwargs)
        self._fs_btn.pack(side="left")

        self._toolbar = toolbar
        self._toolbar_buttons = [self._mute_btn, voldown_btn, volup_btn, self._fs_btn]

    def _toggle_mute(self):
        """Mutes or unmutes the sound and swaps the speaker symbol to match."""
        muted = audio.toggle_mute()
        self._mute_btn.configure(text=_MUTE_ICON if muted else _UNMUTE_ICON)

    def _nudge_volume(self, delta):
        """Turns the volume up or down a notch. Turning it up while muted unmutes."""
        audio.change_volume(delta)
        if audio.is_muted() and delta > 0:
            audio.set_muted(False)
            self._mute_btn.configure(text=_UNMUTE_ICON)

    def _toggle_fullscreen(self):
        """Flips in and out of fullscreen and updates the fullscreen button's symbol."""
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)
        self._fs_btn.configure(text=_EXIT_FULLSCREEN_ICON if self._fullscreen else _FULLSCREEN_ICON)
        self._toolbar.lift()

    def _exit_fullscreen(self, event=None):
        """Escape key: leaves fullscreen if we're in it, otherwise does nothing."""
        if self._fullscreen:
            self._fullscreen = False
            self.attributes("-fullscreen", False)
            self._fs_btn.configure(text=_FULLSCREEN_ICON)
            self._toolbar.lift()

    def _restyle_toolbar(self):
        """Repaints the toolbar buttons in the current accent color. The toolbar isn't
        rebuilt when the accent changes, so this does it by hand."""
        for btn in self._toolbar_buttons:
            btn.configure(fg=theme.GOLD, activeforeground=theme.GOLD)

    # ---------- app icon ----------

    def _apply_app_icon(self):
        """Puts the app's own icon on the window and taskbar (Windows). If there's no
        icon file, or it can't be loaded, the normal Python icon just stays."""
        icon_path = _find_app_icon()
        if icon_path is None:
            return
        try:
            self.iconbitmap(default=str(icon_path))
            return
        except tk.TclError:
            pass
        # Backup plan: load it with Pillow and hand tkinter a regular picture instead.
        try:
            from PIL import Image, ImageTk
            self._app_icon_photo = ImageTk.PhotoImage(Image.open(icon_path).convert("RGBA"))
            self.iconphoto(True, self._app_icon_photo)
        except Exception:
            pass

    def _build_watermark(self):
        """Makes the tiny, faint 'Made by Mrit' tag. tkinter can't do see-through
        widgets, so it fakes it by mixing the colors toward the background."""
        box_bg = theme.blend(theme.PANEL, theme.BG, 0.30)
        text_fg = theme.blend(theme.DIM, theme.BG, 0.55)
        self._watermark_box = tk.Frame(self, bg=box_bg)
        self._watermark = tk.Label(self._watermark_box, text="Made by Mrit", fg=text_fg, bg=box_bg,
                                     font=theme.font(theme.SANS, 6))
        self._watermark.pack(padx=theme.S(5), pady=theme.S(1))
        self._position_watermark("greeting")

    def _position_watermark(self, screen_name):
        """Moves the watermark to whichever corner is free on the given screen."""
        if screen_name in _WATERMARK_BOTTOM_CENTER:
            self._watermark_box.place(relx=0.5, rely=1.0, y=-theme.S(3), anchor="s")
        elif screen_name in _WATERMARK_BOTTOM_LEFT:
            self._watermark_box.place(relx=0.0, rely=1.0, x=theme.S(10), y=-theme.S(3), anchor="sw")
        else:
            self._watermark_box.place(relx=1.0, rely=1.0, x=-theme.S(10), y=-theme.S(3), anchor="se")

    # ---------- accent color (theme picker on Greeting) ----------

    def set_accent(self, hex_color):
        """Changes the accent color everywhere: the theme, the toolbar, and a rebuild
        of the current screen so it picks the new color up."""
        theme.set_accent(hex_color)
        theme.apply_ttk_style(self)
        self._restyle_toolbar()
        if self._current_screen_name:
            self.show_screen(self._current_screen_name)

    # ---------- data / state ----------

    def _load_data(self):
        """Loads the player CSV and the character list, then starts a fresh tournament."""
        if PLAYERS_CSV.exists():
            self.players = load_players(PLAYERS_CSV)
        if ROSTER_JSON.exists():
            self.roster = load_roster(ROSTER_JSON)
        self.reset_tournament()

    def reset_tournament(self):
        """Starts over: one empty team per captain in the CSV, and everything else cleared."""
        self.teams = [
            Team(captain=p, name=f"{p.twitch}'s Team")
            for p in self.players if p.captain
        ]
        self.tournament_type = None
        self.bracket_type = None
        self.bracket = None
        self.bracket_order = None
        self.bracket_settings_origin = None

    def unassigned_players(self):
        """Gives back the non-captains who aren't on a team yet, best rank first."""
        assigned = {p.ign for t in self.teams for p in t.slots if p is not None}
        pool = [p for p in self.players if not p.captain and p.ign not in assigned]
        pool.sort(key=lambda p: rank_sort_key(p.peak_rank))
        return pool

    def show_screen(self, name: str):
        """Swaps in the named screen, replacing the current one, and keeps the
        toolbar, watermark and music in step with it."""
        from app.screens import (
            greeting, seeding, tournament_type,
            mystery_spin, bracket_settings, bracket, congrats,
        )

        screens = {
            "greeting": greeting.GreetingScreen,
            "seeding": seeding.SeedingScreen,
            "tournament_type": tournament_type.TournamentTypeScreen,
            "mystery_spin": mystery_spin.MysterySpinScreen,
            "bracket_settings": bracket_settings.BracketSettingsScreen,
            "bracket": bracket.BracketScreen,
            "congrats": congrats.CongratsScreen,
        }
        theme.set_active_screen(name)
        if self._current_screen is not None:
            self._current_screen.destroy()
        self._current_screen = screens[name](self._container, self)
        self._current_screen.pack(fill="both", expand=True)
        self._current_screen_name = name
        self._position_watermark(name)
        self._toolbar.lift()
        self._watermark_box.lift()
        audio.play_music_for_screen(name)
