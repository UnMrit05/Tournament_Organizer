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
from app.ui import theme

BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
ICONS_DIR = ASSETS_DIR / "icons"

PLAYERS_CSV = DATA_DIR / "players.csv"
ROSTER_JSON = DATA_DIR / "characters.json"
INFO_TXT = ASSETS_DIR / "tournament_info.txt"

APP_VERSION = "0.27"


class TournamentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Rivals Community Tournament v{APP_VERSION}")
        self.configure(bg=theme.BG)

        scale_override = self._read_scale_override()
        theme.init_scale(self, scale_override)
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

        self._build_fullscreen_control()

        self._load_data()
        self.show_screen("greeting")

    def _read_scale_override(self):
        if INFO_TXT.exists():
            for line in INFO_TXT.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.lower().startswith("scale:"):
                    try:
                        return float(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
        return None

    def _build_fullscreen_control(self):
        """A persistent top-right button (outside any screen, so it
        survives navigation) toggling true fullscreen. Escape exits it."""
        self._fullscreen = False
        self.bind("<Escape>", self._exit_fullscreen)
        self._fs_btn = tk.Button(self, text="\u26F6", command=self._toggle_fullscreen,
                                   bg=theme.PANEL_2, fg=theme.TEXT, activebackground=theme.LINE,
                                   relief="flat", bd=0, cursor="hand2",
                                   font=theme.font(theme.SANS, 12),
                                   padx=theme.S(8), pady=theme.S(4))
        self._fs_btn.place(relx=1.0, x=-theme.S(14), y=theme.S(10), anchor="ne")

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)
        self._fs_btn.configure(text="\u2715" if self._fullscreen else "\u26F6")
        self._fs_btn.lift()

    def _exit_fullscreen(self, event=None):
        if self._fullscreen:
            self._fullscreen = False
            self.attributes("-fullscreen", False)
            self._fs_btn.configure(text="\u26F6")
            self._fs_btn.lift()

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
        self._fs_btn.lift()
