"""Screen 7 - Congratulations.

Shown once the bracket has a champion. Displays the winning team's
name and captain plus a short roster/Mystery-Hero summary, with
Back (return to the Bracket screen) and End (close the app) buttons.
"""

import tkinter as tk

from app.ui import theme
from app.ui.player_icons import name_with_platform, role_icons


class CongratsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app
        champion = getattr(app.bracket, "champion", None) if app.bracket else None

        middle = tk.Frame(self, bg=theme.BG)
        middle.pack(side="top", fill="both", expand=True)
        wrap = tk.Frame(middle, bg=theme.BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrap, text="\U0001F3C6", fg=theme.GOLD, bg=theme.BG,
                  font=theme.font(theme.SANS, 46)).pack(pady=(0, 6))
        tk.Label(wrap, text="Congratulations!", fg=theme.TEXT, bg=theme.BG,
                  font=theme.FONT_DISPLAY).pack()

        if champion is None:
            tk.Label(wrap, text="The tournament hasn't crowned a champion yet.",
                      fg=theme.DIM, bg=theme.BG, font=theme.FONT_BODY).pack(pady=(10, 0))
        else:
            tk.Label(wrap, text=f"{champion.name} wins the tournament!", fg=theme.GOLD, bg=theme.BG,
                      font=theme.font(theme.SEMIBOLD, 20)).pack(pady=(10, 2))

            card = tk.Frame(wrap, bg=theme.PANEL, highlightbackground=theme.LINE, highlightthickness=1)
            card.pack(pady=(16, 0))
            inner = tk.Frame(card, bg=theme.PANEL)
            inner.pack(padx=26, pady=18)

            tk.Label(inner, text="Captain", fg=theme.DIM, bg=theme.PANEL,
                      font=theme.FONT_SMALL).pack(anchor="w")
            cap_row = name_with_platform(inner, champion.captain, theme.PANEL,
                                            name_font=theme.font(theme.SEMIBOLD, 16))
            cap_row.pack(anchor="w", pady=(2, 12))

            roster_players = champion.all_players()
            tk.Label(inner, text=f"Roster ({len(roster_players)})", fg=theme.DIM, bg=theme.PANEL,
                      font=theme.FONT_SMALL).pack(anchor="w")
            for p in roster_players:
                row = tk.Frame(inner, bg=theme.PANEL)
                row.pack(fill="x", pady=3)
                name_with_platform(row, p, theme.PANEL).pack(side="left")
                role = champion.player_roles.get(p.ign)
                char = champion.player_characters.get(p.ign)
                if role or char:
                    detail = " / ".join(x for x in (role, char) if x)
                    tk.Label(row, text=detail, fg=theme.DIM, bg=theme.PANEL,
                              font=theme.FONT_SMALL).pack(side="left", padx=(10, 0))
                else:
                    role_icons(row, p, theme.PANEL).pack(side="left", padx=(10, 0))

        btn_row = tk.Frame(wrap, bg=theme.BG)
        btn_row.pack(pady=(24, 0))
        tk.Button(btn_row, text="Back", command=lambda: app.show_screen("bracket"),
                   **theme.button_kwargs()).pack(side="left", padx=6)
        tk.Button(btn_row, text="End", command=app.destroy,
                   **theme.primary_button_kwargs()).pack(side="left", padx=6)
