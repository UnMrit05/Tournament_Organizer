"""The first screen: shows the tournament title and host, with Start, Continue and End buttons, plus a Theme button for picking the accent color."""

import tkinter as tk

from app.app_state import APP_VERSION, LICENSE_NAME, read_config_value
from app.data.save_manager import STATUS_TO_SCREEN, has_save, load_state, restore_app_state
from app.ui import theme
from app.ui.pop_anim import pop_in


class GreetingScreen(tk.Frame):
    """The welcome screen."""
    def __init__(self, parent, app):
        """Lays out the title, the Theme button, the Start/Continue/End buttons and the footer text."""
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
        """Grabs the title and host from app_config.txt (with fallbacks if they're missing)."""
        title = read_config_value("title") or "Community Rivals Tournament"
        host = read_config_value("host") or "Unknown Host"
        return title, host

    # ---------- theme picker ----------

    def _open_theme_picker(self):
        """Pops up the little window for picking a new accent color, either with R/G/B boxes or a hex code."""
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

        tk.Label(pad, text="Accent color (RGB or hex)", fg=theme.TEXT, bg=theme.PANEL,
                  font=theme.FONT_NAME).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        r_var, g_var, b_var = tk.IntVar(value=r0), tk.IntVar(value=g0), tk.IntVar(value=b0)
        hex_var = tk.StringVar(value=f"#{r0:02x}{g0:02x}{b0:02x}")
        swatch = tk.Frame(pad, width=theme.S(48), height=theme.S(48), bg=theme.GOLD,
                            highlightbackground=theme.LINE, highlightthickness=1)
        swatch.grid(row=1, column=3, rowspan=4, padx=(16, 0))

        _syncing = {"on": False}   # guards against the RGB<->hex updates re-triggering each other

        def _clamped(var):
            """Reads a number box and squeezes it into 0-255 (anything weird becomes 0)."""
            try:
                v = int(var.get())
            except (tk.TclError, ValueError):
                v = 0
            v = max(0, min(255, v))
            if v != var.get():
                var.set(v)
            return v

        def _update_preview(*_):
            """Repaints the color swatch and keeps the hex box matching the R/G/B numbers."""
            r, g, b = _clamped(r_var), _clamped(g_var), _clamped(b_var)
            hex_str = f"#{r:02x}{g:02x}{b:02x}"
            swatch.configure(bg=hex_str)
            if not _syncing["on"]:
                _syncing["on"] = True
                hex_var.set(hex_str)
                _syncing["on"] = False

        for i, (label, var) in enumerate((("R", r_var), ("G", g_var), ("B", b_var))):
            tk.Label(pad, text=label, fg=theme.DIM, bg=theme.PANEL,
                      font=theme.FONT_SMALL).grid(row=1 + i, column=0, sticky="w", pady=3)
            spin = tk.Spinbox(pad, from_=0, to=255, textvariable=var, width=5,
                                bg=theme.PANEL_2, fg=theme.TEXT, insertbackground=theme.TEXT,
                                relief="flat", font=theme.FONT_SMALL, command=_update_preview)
            spin.grid(row=1 + i, column=1, padx=(6, 0), pady=3)
            var.trace_add("write", _update_preview)

        def _apply_hex(*_):
            """If the hex box has a proper 6-digit code, copies it into the R/G/B boxes."""
            text = hex_var.get().strip().lstrip("#")
            if len(text) == 6 and all(c in "0123456789abcdefABCDEF" for c in text):
                _syncing["on"] = True
                r_var.set(int(text[0:2], 16))
                g_var.set(int(text[2:4], 16))
                b_var.set(int(text[4:6], 16))
                _syncing["on"] = False
                _update_preview()

        tk.Label(pad, text="Hex", fg=theme.DIM, bg=theme.PANEL,
                  font=theme.FONT_SMALL).grid(row=4, column=0, sticky="w", pady=3)
        hex_entry = tk.Entry(pad, textvariable=hex_var, width=8, bg=theme.PANEL_2, fg=theme.TEXT,
                               insertbackground=theme.TEXT, relief="flat", font=theme.FONT_SMALL)
        hex_entry.grid(row=4, column=1, padx=(6, 0), pady=3, sticky="w")
        hex_entry.bind("<Return>", _apply_hex)
        hex_entry.bind("<FocusOut>", _apply_hex)

        btn_row = tk.Frame(pad, bg=theme.PANEL)
        btn_row.grid(row=5, column=0, columnspan=4, sticky="e", pady=(16, 0))

        def _apply():
            # Commit whatever's typed in the hex box first, so clicking Apply
            # straight after typing (no Enter/Tab) still uses it.
            """Applies the chosen color to the whole app and closes the picker."""
            _apply_hex()
            r, g, b = _clamped(r_var), _clamped(g_var), _clamped(b_var)
            self.app.set_accent(f"#{r:02x}{g:02x}{b:02x}")
            top.destroy()

        tk.Button(btn_row, text="Cancel", command=top.destroy, **theme.button_kwargs()).pack(
            side="left", padx=4)
        tk.Button(btn_row, text="Apply", command=_apply, **theme.primary_button_kwargs()).pack(
            side="left", padx=4)

    def _on_start(self):
        """Starts a fresh tournament and goes to Drafting."""
        self.app.reset_tournament()
        self.app.show_screen("seeding")

    def _on_continue(self):
        # Load the saved state, then jump to the stage the save was made at.
        """Loads the saved tournament and jumps back to wherever you left off."""
        self.app.reset_tournament()
        status = restore_app_state(self.app, load_state())
        self.app.show_screen(STATUS_TO_SCREEN.get(status, "seeding"))

    def _on_end(self):
        """Closes the app."""
        self.app.destroy()
