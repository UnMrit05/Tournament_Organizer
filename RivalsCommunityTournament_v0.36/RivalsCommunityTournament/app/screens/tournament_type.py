"""The tournament type screen: choose Mystery Hero (spin for roles/characters) or Normal (straight to bracket settings)."""

import tkinter as tk

from app.ui import theme


class TournamentTypeScreen(tk.Frame):
    """Screen with the Mystery Hero, Normal and Back buttons."""
    def __init__(self, parent, app):
        """Builds the title and the buttons."""
        super().__init__(parent, bg=theme.BG)
        self.app = app

        wrap = tk.Frame(self, bg=theme.BG)
        wrap.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(wrap, text="Select tournament type", fg=theme.TEXT, bg=theme.BG,
                  font=theme.FONT_HEADING).pack(pady=(0, 26))

        btns = tk.Frame(wrap, bg=theme.BG)
        btns.pack()

        mystery_kwargs = theme.primary_button_kwargs()
        mystery_kwargs.update(padx=theme.S(30), pady=theme.S(16), font=theme.font(theme.SEMIBOLD, 13))
        normal_kwargs = theme.button_kwargs()
        normal_kwargs.update(padx=theme.S(30), pady=theme.S(16), font=theme.font(theme.SEMIBOLD, 13))

        tk.Button(btns, text="Mystery Hero", command=self._pick_mystery,
                   **mystery_kwargs).pack(side="left", padx=8)
        tk.Button(btns, text="Normal", command=self._pick_normal,
                   **normal_kwargs).pack(side="left", padx=8)

        tk.Button(wrap, text="Back", command=lambda: app.show_screen("seeding"),
                   **theme.button_kwargs()).pack(pady=(28, 0))

    def _pick_mystery(self):
        """Picks Mystery Hero and goes to the spin screen."""
        self.app.tournament_type = "mystery"
        self.app.show_screen("mystery_spin")

    def _pick_normal(self):
        """Picks Normal and goes straight to bracket settings."""
        self.app.tournament_type = "normal"
        # Remember we skipped Mystery Hero, so Bracket Settings' Back button
        # comes back here instead of going to Mystery Hero.
        self.app.bracket_settings_origin = "tournament_type"
        self.app.show_screen("bracket_settings")
