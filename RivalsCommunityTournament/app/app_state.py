"""Root window, shared application state, and screen router.

Screens are simple tk.Frame subclasses that read/write attributes on
this TournamentApp instance (self.app inside a screen) rather than
passing data through constructors, so any screen can reach the full
tournament state.
"""

import tkinter as tk
from pathlib import Path

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
INFO_TXT = ASSETS_DIR / "tournament_info.txt"

APP_VERSION = "0.30"
LICENSE_NAME = "MIT License"

_MUTE_ICON = "\U0001F507"      # muted speaker
_UNMUTE_ICON = "\U0001F50A"    # speaker, high volume
_FULLSCREEN_ICON = "⛶"
_EXIT_FULLSCREEN_ICON = "✕"


class TournamentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Rivals Community Tournament v{APP_VERSION}")
        self.configure(bg=theme.BG)

        scale_override = self._read_info_override("scale")
        theme.init_scale(self, scale_override)
        font_override = self._read_info_override("font", as_float=False)
        if font_override:
            theme.set_custom_font(font_override)
        theme.apply_ttk_style(self)

        self.geometry(f"{theme.S(1100)}x{theme.S(720)}")
        self.minsize(theme.S(860), theme.S(600))
        try:
            self.state("zoomed")  # fill the screen by default (Windows)
        except tk.TclError:
            pass

        # Shared state carried between screens.
        self.players = []          # list[app.data.players.Player]
        self.roster = []           # list[app.data.roster.Character]
        self.teams = []            # filled in during Drafting
        self.tournament_type = None    # "mystery" | "normal"
        self.bracket_type = None       # "single" | "double" | "league"
        self.bracket = None
        self.bracket_order = None      # teams in seed order (Bracket Settings)

        self._container = tk.Frame(self, bg=theme.BG)
        self._container.pack(fill="both", expand=True)
        self._current_screen = None
        self._current_screen_name = None

        self._build_toolbar()
        self._build_watermark()

        # One click sound for every tk.Button in the app, without touching
        # individual button code: bind_class adds to ALL widgets of that
        # class. add="+" keeps each button's own command intact.
        self.bind_class("Button", "<Button-1>", audio.play_click, add="+")

        self._load_data()
        self.show_screen("greeting")

    def _read_info_override(self, key, as_float=True):
        if not INFO_TXT.exists():
            return None
        prefix = f"{key}:".lower()
        for line in INFO_TXT.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.lower().startswith(prefix):
                value = line.split(":", 1)[1].strip()
                if not as_float:
                    return value or None
                try:
                    return float(value)
                except ValueError:
                    return None
        return None

    # ---------- top-right toolbar: Mute, Vol+, Vol-, Fullscreen ----------

    def _build_toolbar(self):
        """A persistent toolbar (outside any screen, so it survives
        navigation), left to right: Mute/Unmute, Volume Up, Volume Down,
        Fullscreen/Cross. Every button shares the same size so nothing in
        the row overlaps or hangs off-size next to the others."""
        self._fullscreen = False
        self.bind("<Escape>", self._exit_fullscreen)

        btn_kwargs = dict(bg=theme.PANEL_2, fg=theme.TEXT, activebackground=theme.LINE,
                           relief="flat", bd=0, cursor="hand2", width=2,
                           font=theme.font(theme.SANS, 12),
                           padx=theme.S(6), pady=theme.S(4))

        toolbar = tk.Frame(self, bg=theme.BG)
        toolbar.place(relx=1.0, x=-theme.S(14), y=theme.S(10), anchor="ne")

        self._mute_btn = tk.Button(toolbar, text=_UNMUTE_ICON, command=self._toggle_mute, **btn_kwargs)
        self._mute_btn.pack(side="left", padx=(0, theme.S(4)))
        tk.Button(toolbar, text="+", command=lambda: self._nudge_volume(0.1), **btn_kwargs).pack(
            side="left", padx=(0, theme.S(4)))
        tk.Button(toolbar, text="−", command=lambda: self._nudge_volume(-0.1), **btn_kwargs).pack(
            side="left", padx=(0, theme.S(4)))
        self._fs_btn = tk.Button(toolbar, text=_FULLSCREEN_ICON, command=self._toggle_fullscreen, **btn_kwargs)
        self._fs_btn.pack(side="left")

        self._toolbar = toolbar

    def _toggle_mute(self):
        muted = audio.toggle_mute()
        self._mute_btn.configure(text=_MUTE_ICON if muted else _UNMUTE_ICON)

    def _nudge_volume(self, delta):
        audio.change_volume(delta)
        if audio.is_muted() and delta > 0:
            audio.set_muted(False)
            self._mute_btn.configure(text=_UNMUTE_ICON)

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)
        self._fs_btn.configure(text=_EXIT_FULLSCREEN_ICON if self._fullscreen else _FULLSCREEN_ICON)
        self._toolbar.lift()

    def _exit_fullscreen(self, event=None):
        if self._fullscreen:
            self._fullscreen = False
            self.attributes("-fullscreen", False)
            self._fs_btn.configure(text=_FULLSCREEN_ICON)
            self._toolbar.lift()

    def _build_watermark(self):
        self._watermark = tk.Label(self, text="Made by Mrit", fg=theme.DIM, bg=theme.BG,
                                     font=theme.font(theme.SANS, 8))
        self._watermark.place(relx=1.0, rely=1.0, x=-theme.S(8), y=-theme.S(6), anchor="se")

    # ---------- accent color (theme picker on Greeting) ----------

    def set_accent(self, hex_color):
        """Replace the accent color everywhere and rebuild the current
        screen so its widgets pick the new color up immediately."""
        theme.set_accent(hex_color)
        theme.apply_ttk_style(self)
        if self._current_screen_name:
            self.show_screen(self._current_screen_name)

    # ---------- data / state ----------

    def _load_data(self):
        if PLAYERS_CSV.exists():
            self.players = load_players(PLAYERS_CSV)
        if ROSTER_JSON.exists():
            self.roster = load_roster(ROSTER_JSON)
        self.reset_tournament()

    def reset_tournament(self):
        """Fresh draft: rebuild every team from the captains in the CSV and
        clear all tournament-level state."""
        self.teams = [
            Team(captain=p, name=f"{p.ign}'s Team")
            for p in self.players if p.captain
        ]
        self.tournament_type = None
        self.bracket_type = None
        self.bracket = None
        self.bracket_order = None

    def unassigned_players(self):
        """Non-captain players not yet placed in any team's slots,
        sorted highest rank first."""
        assigned = {p.ign for t in self.teams for p in t.slots if p is not None}
        pool = [p for p in self.players if not p.captain and p.ign not in assigned]
        pool.sort(key=lambda p: rank_sort_key(p.peak_rank))
        return pool

    def show_screen(self, name: str):
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
        if self._current_screen is not None:
            self._current_screen.destroy()
        self._current_screen = screens[name](self._container, self)
        self._current_screen.pack(fill="both", expand=True)
        self._current_screen_name = name
        self._toolbar.lift()
        self._watermark.lift()
        audio.play_music_for_screen(name)
