"""The main window. Holds the shared tournament state, the top-right toolbar
(light/dark, sound, full screen), and switches between screens."""

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
from app.ui import audio, dialogs, fonts, gfx, prefs, text, theme
from app.ui.text import read_config_value
from app.ui.widgets import ToolButton

BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
ICONS_DIR = ASSETS_DIR / "icons"

PLAYERS_CSV = DATA_DIR / "players.csv"
ROSTER_JSON = DATA_DIR / "characters.json"
CONFIG_TXT = ASSETS_DIR / "app_config.txt"

APP_VERSION = "0.43"
LICENSE_NAME = "MIT License"

# Windows groups taskbar buttons by this id. Giving the app its own means it
# gets its own icon instead of sharing Python's.
_APP_USER_MODEL_ID = "RivalsCommunityTournament.App"

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

# Names the "Theme:" line in app_config.txt can go by.
_THEME_KEYS = ("theme", "default theme", "theme color", "theme colour",
               "accent", "accent color", "accent colour")

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
        """Sets up the window, reads app_config.txt, builds the toolbar, loads the
        data, and shows the Greeting screen."""
        _set_windows_app_id()
        fonts.register_local_fonts()
        super().__init__()
        self.title(f"Rivals Community Tournament v{APP_VERSION}")

        theme.init_scale(self, self._read_info_override("scale"))
        font_override = self._read_info_override("font", as_float=False)
        if font_override:
            theme.set_custom_font(font_override)
        font_size_override = self._read_info_override("font size", as_float=True)
        if font_size_override:
            theme.set_font_size_mult(font_size_override)
        heading_fonts, body_fonts = self._read_screen_fonts()
        theme.set_screen_fonts(heading_fonts, body_fonts)

        # Optional starting accent colors from the config file. "Theme:" applies to
        # both modes; "Theme Dark:" / "Theme Light:" only set the stock color of that mode.
        theme.set_stock_accents(self._normalize_color(read_config_value("theme dark")),
                                self._normalize_color(read_config_value("theme light")))
        theme_color = self._normalize_color(read_config_value(*_THEME_KEYS))
        if theme_color:
            theme.set_accent(theme_color)

        # Light or dark: the last choice wins, otherwise the config's Start Mode (dark if missing).
        remembered = prefs.load().get("mode")
        theme.set_mode(remembered if remembered in ("dark", "light") else self._start_mode())
        gfx.set_sparkles(text.flag("Sparkles", default=False))
        gfx.set_grain(text.flag("Grain"))
        self.configure(bg=theme.BG)

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
        self._prewarmed = False
        self.intro_pending = True

        self._build_toolbar()
        self.protocol("WM_DELETE_WINDOW", self.request_close)

        # One click sound for every tk.Button in the app, without touching
        # each button: bind_class covers all of them, and add="+" keeps each
        # button's own command working.
        self.bind_class("Button", "<Button-1>", self._click_sound, add="+")

        self._load_data()
        self.show_screen("greeting")

    def _click_sound(self, event):
        """Plays the click sound for a button press, unless that button is switched off."""
        if getattr(event.widget, "_enabled", True):
            audio.play_click(event)

    def _read_info_override(self, key, as_float=True):
        """Reads one setting from app_config.txt. Gives back a number (or None if
        it isn't one) when as_float is True, otherwise the raw text (or None)."""
        value = read_config_value(key)
        return _to_float(value) if as_float else value

    def _start_mode(self):
        """The mode to open in the very first time (before any choice is remembered): 'light' or 'dark'."""
        value = (read_config_value("start mode") or "dark").strip().lower()
        return "light" if value == "light" else "dark"

    def _normalize_color(self, value):
        """Turns a color from the config file ('#3FA7FF', '3fa7ff', '#fff' or a name
        like 'blue') into a plain '#rrggbb' string. Gives back None if it isn't a real color."""
        if not value:
            return None
        color_text = value.split()[0].strip("\"'")
        if re.fullmatch(r"[0-9a-fA-F]{6}|[0-9a-fA-F]{3}", color_text):
            color_text = "#" + color_text
        try:
            r, g, b = self.winfo_rgb(color_text)
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

    # ---------- top-right toolbar: light/dark, mute, volume down, volume up, full screen ----------

    def _build_toolbar(self):
        """Builds the five little square buttons in the top-right corner. They live on the
        main window, not on a screen, so they stay put when you switch screens."""
        self._fullscreen = False
        self.bind("<Escape>", self._exit_fullscreen)

        self._mode_btn = ToolButton(self, self._mode_icon(), self.toggle_mode, self._mode_tip())
        self._mute_btn = ToolButton(self, self._sound_icon(), self._toggle_mute, self._mute_tip())
        voldown_btn = ToolButton(self, "minus", lambda: self._nudge_volume(-0.1), text.t("Tip Volume Down"))
        volup_btn = ToolButton(self, "plus", lambda: self._nudge_volume(0.1), text.t("Tip Volume Up"))
        self._fs_btn = ToolButton(self, "full", self._toggle_fullscreen, text.t("Tip Full Screen"))
        self._toolbar_buttons = [self._mode_btn, self._mute_btn, voldown_btn, volup_btn, self._fs_btn]
        self._position_toolbar()

    def _position_toolbar(self):
        """Places the five buttons in a row against the top-right corner, lined up with the header."""
        size, gap = theme.S(theme.SQUARE), theme.S(theme.SP_2)
        count = len(self._toolbar_buttons)
        top = theme.S(theme.MARGIN) + (theme.S(theme.HEADER_H) - size) // 2
        for i, btn in enumerate(self._toolbar_buttons):
            offset = theme.S(theme.MARGIN) + (count - 1 - i) * (size + gap)
            btn.place(relx=1.0, x=-offset, y=top, anchor="ne")

    def _lift_toolbar(self):
        """Keeps the toolbar on top of whatever screen is showing."""
        for btn in self._toolbar_buttons:
            btn.lift()

    def _mode_icon(self):
        """The icon for the light/dark button: a moon in dark mode (click for light), a sun in light mode."""
        return "moon" if theme.MODE == "dark" else "sun"

    def _mode_tip(self):
        """The hover hint for the light/dark button."""
        return text.t("Tip Light Mode") if theme.MODE == "dark" else text.t("Tip Dark Mode")

    def _sound_icon(self):
        """The icon for the sound button: muted speaker or normal speaker."""
        return "mute" if audio.is_muted() else "sound"

    def _mute_tip(self):
        """The hover hint for the sound button."""
        return text.t("Tip Unmute") if audio.is_muted() else text.t("Tip Mute")

    def _toggle_mute(self):
        """Mutes or unmutes the sound and swaps the speaker symbol to match."""
        audio.toggle_mute()
        self._mute_btn.set_icon(self._sound_icon(), self._mute_tip())

    def _nudge_volume(self, delta):
        """Turns the volume up or down a notch. Turning it up while muted unmutes."""
        audio.change_volume(delta)
        if audio.is_muted() and delta > 0:
            audio.set_muted(False)
            self._mute_btn.set_icon(self._sound_icon(), self._mute_tip())

    def _toggle_fullscreen(self):
        """Flips in and out of fullscreen and updates the fullscreen button's symbol."""
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)
        self._fs_btn.set_icon("exitfull" if self._fullscreen else "full",
                              text.t("Tip Exit Full Screen") if self._fullscreen else text.t("Tip Full Screen"))
        self._lift_toolbar()

    def _exit_fullscreen(self, event=None):
        """Escape key: leaves fullscreen if we're in it, otherwise does nothing."""
        if self._fullscreen:
            self._toggle_fullscreen()

    def _restyle_toolbar(self):
        """Repaints the toolbar buttons for the current mode and accent color. The toolbar isn't
        rebuilt when those change, so this does it by hand."""
        self._mode_btn.set_icon(self._mode_icon(), self._mode_tip())
        for btn in self._toolbar_buttons[1:]:
            btn.refresh()

    # ---------- light / dark mode ----------

    def toggle_mode(self):
        """Switches between light and dark mode, remembers the choice for next time, and repaints."""
        screen = self._current_screen
        if screen is not None and getattr(screen, "is_busy", lambda: False)():
            return
        theme.set_mode("light" if theme.MODE == "dark" else "dark")
        prefs.save(mode=theme.MODE)
        self._repaint()

    def _repaint(self):
        """Re-themes everything after a mode or accent change: window, dropdowns, toolbar and the current screen."""
        self.configure(bg=theme.BG)
        self._container.configure(bg=theme.BG)
        theme.apply_ttk_style(self)
        self._restyle_toolbar()
        if self._current_screen_name:
            kept = self._current_screen.capture_state() if self._current_screen is not None else None
            self.show_screen(self._current_screen_name, keep_state=kept)

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

    # ---------- accent color (theme picker on Greeting) ----------

    def set_accent(self, hex_color):
        """Changes the accent color everywhere: the theme, the toolbar, and a rebuild
        of the current screen so it picks the new color up."""
        theme.set_accent(hex_color)
        self._repaint()

    # ---------- closing the app ----------

    def request_close(self):
        """Every way of closing the app goes through here: it warns that unsaved work will be lost,
        and only closes if the person presses OK."""
        if dialogs.confirm_unsaved(self):
            self.destroy()

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

    def show_screen(self, name: str, keep_state=None):
        """Swaps in the named screen. The new one is built and laid out first and the old one
        is removed after, so there's no blank flash. Also keeps the toolbar and music in step.
        keep_state is what the old copy of this screen handed over (used when only the colors changed)."""
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
        self.intro_pending = keep_state is None     # headings only pop in when you arrive, not after a color change
        old = self._current_screen
        width = self._container.winfo_width()
        height = self._container.winfo_height()
        if width < 50 or height < 50:
            width, height = self.winfo_screenwidth(), self.winfo_screenheight()
        new = screens[name](self._container, self)
        new.place(x=0, y=0, relwidth=1, relheight=1)
        new.relayout(width, height)
        if keep_state:
            new.restore_state(keep_state)
        self._current_screen = new
        self._current_screen_name = name
        self._lift_toolbar()
        if old is not None:
            self.update_idletasks()
            old.destroy()
        audio.play_music_for_screen(name)
        if not self._prewarmed:
            self._prewarmed = True
            self.after(700, self._prewarm)

    def _prewarm(self):
        """While the app is idle, draws the backgrounds that will be wanted next (the other color mode, and the
        full screen / windowed sizes) one at a time, so switching to them later is instant."""
        wide, high = self.winfo_screenwidth(), self.winfo_screenheight()
        here = (max(8, self._container.winfo_width()), max(8, self._container.winfo_height()))
        other = "light" if theme.MODE == "dark" else "dark"
        jobs = [(wide, high, theme.MODE), (here[0], here[1], other), (wide, high, other)]

        def step():
            """Draws the next waiting background, then schedules the one after it."""
            if jobs:
                w, h, mode = jobs.pop(0)
                try:
                    gfx.prewarm_background(w, h, mode)
                except Exception:
                    return
                self.after(250, step)
        step()

    def request_home(self):
        """The Home button: after the unsaved-changes warning, wipes this tournament and goes back to the start screen."""
        if dialogs.confirm_unsaved(self, home=True):
            self.reset_tournament()
            self.show_screen("greeting")
