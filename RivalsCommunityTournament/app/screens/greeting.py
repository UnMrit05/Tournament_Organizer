"""Screen 1 — Greeting.

Reads title/host from assets/tournament_info.txt. Start begins a
fresh seeding bracket. Continue loads the saved seeding/bracket data
if a save file is present (disabled otherwise). End closes the app.
"""

import tkinter as tk

from app.app_state import INFO_TXT
from app.data.save_manager import STATUS_TO_SCREEN, has_save, load_state, restore_app_state
from app.ui import theme


class GreetingScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app

        title, host = self._read_info()

        wrap = tk.Frame(self, bg=theme.BG)
        wrap.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(wrap, text=f"Hosted by {host}", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(pady=(0, 6))
        tk.Label(wrap, text=title, fg=theme.TEXT, bg=theme.BG,
                  font=theme.FONT_DISPLAY).pack(pady=(0, 28))

        btns = tk.Frame(wrap, bg=theme.BG)
        btns.pack()

        tk.Button(btns, text="Start", command=self._on_start,
                   **theme.primary_button_kwargs()).pack(side="left", padx=6)

        continue_btn = tk.Button(btns, text="Continue", command=self._on_continue,
                                   **theme.button_kwargs())
        continue_btn.pack(side="left", padx=6)
        if not has_save():
            continue_btn.configure(state="disabled")

        tk.Button(btns, text="End", command=self._on_end,
                   **theme.button_kwargs()).pack(side="left", padx=6)

    def _read_info(self):
        title, host = "Community Rivals Tournament", "Unknown Host"
        if INFO_TXT.exists():
            for line in INFO_TXT.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.lower().startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.lower().startswith("host:"):
                    host = line.split(":", 1)[1].strip()
        return title, host

    def _on_start(self):
        self.app.reset_tournament()
        self.app.show_screen("seeding")

    def _on_continue(self):
        # Restore the saved draft/spin/bracket-setting state, then jump to
        # the stage the save was made at.
        self.app.reset_tournament()
        status = restore_app_state(self.app, load_state())
        self.app.show_screen(STATUS_TO_SCREEN.get(status, "seeding"))

    def _on_end(self):
        self.app.destroy()
