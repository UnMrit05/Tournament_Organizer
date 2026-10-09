"""Screen 1 — Greeting.

Reads title/host from assets/tournament_info.txt. Start begins a
fresh seeding bracket. Continue loads the saved seeding/bracket data
if a save file is present (disabled otherwise). End closes the app.

v0.30: a theme button at the top-left opens an RGB color picker that
replaces the accent color used everywhere (default: gold); the title
pops in on open; the bottom of the screen states the app's license and
version.
"""

import tkinter as tk

from app.app_state import APP_VERSION, INFO_TXT, LICENSE_NAME
from app.data.save_manager import STATUS_TO_SCREEN, has_save, load_state, restore_app_state
from app.ui import theme
from app.ui.pop_anim import pop_in


class GreetingScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app

        title, host = self._read_info()

        self._theme_btn = tk.Button(self, text="\U0001F3A8 Theme", command=self._open_theme_picker,
                                      **theme.button_kwargs())
        self._theme_btn.place(x=theme.S(16), y=theme.S(14), anchor="nw")

        wrap = tk.Frame(self, bg=theme.BG)
        wrap.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(wrap, text=f"Hosted by {host}", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(pady=(0, 6))
        self._title_lbl = tk.Label(wrap, text=title, fg=theme.TEXT, bg=theme.BG)
        self._title_lbl.pack(pady=(0, 28))
        pop_in(self._title_lbl, theme.SEMIBOLD, 26)

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

        tk.Label(self, text=f"Open-source software ({LICENSE_NAME}) — v{APP_VERSION}",
                  fg=theme.DIM, bg=theme.BG, font=theme.FONT_SMALL).pack(side="bottom", pady=(0, 14))

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

    # ---------- theme picker ----------

    def _open_theme_picker(self):
        try:
            r0 = int(theme.GOLD[1:3], 16)
            g0 = int(theme.GOLD[3:5], 16)
            b0 = int(theme.GOLD[5:7], 16)
        except (ValueError, IndexError):
            r0, g0, b0 = 232, 184, 84

        top = tk.Toplevel(self)
        top.title("Accent Color")
        top.configure(bg=theme.PANEL)
        top.transient(self.winfo_toplevel())
        top.resizable(False, False)

        pad = tk.Frame(top, bg=theme.PANEL)
        pad.pack(padx=18, pady=16)

        tk.Label(pad, text="Accent color (RGB)", fg=theme.TEXT, bg=theme.PANEL,
                  font=theme.FONT_NAME).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        r_var, g_var, b_var = tk.IntVar(value=r0), tk.IntVar(value=g0), tk.IntVar(value=b0)
        swatch = tk.Frame(pad, width=theme.S(48), height=theme.S(48), bg=theme.GOLD,
                            highlightbackground=theme.LINE, highlightthickness=1)
        swatch.grid(row=1, column=3, rowspan=3, padx=(16, 0))

        def _clamped(var):
            try:
                v = int(var.get())
            except (tk.TclError, ValueError):
                v = 0
            v = max(0, min(255, v))
            if v != var.get():
                var.set(v)
            return v

        def _update_preview(*_):
            r, g, b = _clamped(r_var), _clamped(g_var), _clamped(b_var)
            swatch.configure(bg=f"#{r:02x}{g:02x}{b:02x}")

        for i, (label, var) in enumerate((("R", r_var), ("G", g_var), ("B", b_var))):
            tk.Label(pad, text=label, fg=theme.DIM, bg=theme.PANEL,
                      font=theme.FONT_SMALL).grid(row=1 + i, column=0, sticky="w", pady=3)
            spin = tk.Spinbox(pad, from_=0, to=255, textvariable=var, width=5,
                                bg=theme.PANEL_2, fg=theme.TEXT, insertbackground=theme.TEXT,
                                relief="flat", font=theme.FONT_SMALL, command=_update_preview)
            spin.grid(row=1 + i, column=1, padx=(6, 0), pady=3)
            var.trace_add("write", _update_preview)

        btn_row = tk.Frame(pad, bg=theme.PANEL)
        btn_row.grid(row=4, column=0, columnspan=4, sticky="e", pady=(16, 0))

        def _apply():
            r, g, b = _clamped(r_var), _clamped(g_var), _clamped(b_var)
            self.app.set_accent(f"#{r:02x}{g:02x}{b:02x}")
            top.destroy()

        tk.Button(btn_row, text="Cancel", command=top.destroy, **theme.button_kwargs()).pack(
            side="left", padx=4)
        tk.Button(btn_row, text="Apply", command=_apply, **theme.primary_button_kwargs()).pack(
            side="left", padx=4)

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
