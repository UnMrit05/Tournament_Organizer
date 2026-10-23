"""The first screen: the tournament title and host, with Start, Continue and End buttons, a Theme button for picking the accent color, and a summary of what was read from players.csv."""

import tkinter as tk

from app.data.save_manager import STATUS_TO_SCREEN, has_save, load_state, restore_app_state
from app.ui import picker, text, theme
from app.ui.pop_anim import pop_in
from app.ui.stage import POP_DELAY_MS, Stage
from app.ui.widgets import AccentBar, Chip, GlassButton, Panel

APP_LICENSE = "MIT License"
HERO_W = 816


class GreetingScreen(Stage):
    """The welcome screen."""

    STEP = None
    WATERMARK = "right"
    HEADER_LINE = False
    HAS_HOME = False

    def __init__(self, parent, app):
        """Lays out the Theme button, the big title panel with Start/Continue/End, the players.csv chips and the footer text."""
        super().__init__(parent, app, "greeting")
        from app.app_state import APP_VERSION

        title = text.t("Title")
        host = text.t("Host")

        self._theme_btn = GlassButton(self, text.t("Button Theme"), self._open_theme_picker,
                                      kind="secondary", height=32, icon="swatch", pad=16,
                                      font=theme.fpx(theme.SEMIBOLD, 12), minimum=0)
        self.put(self._theme_btn, lambda: (self.margin(), self.header_top() + theme.S(4),
                                           self._theme_btn.pixel_width, theme.S(32)))

        self._hero = Panel(self, stripe=False)
        self._build_hero(self._hero.body, title, host)
        self._hero.update_idletasks()
        self._hero_h = self._hero.winfo_reqheight()
        self.put(self._hero, self._hero_rect)

        self._compass = []
        self.hook(self._draw_compass)

        footer = text.t("Footer", license=APP_LICENSE, version=APP_VERSION)
        self._footer_item = self.create_text(0, 0, anchor="sw", text=footer, fill=theme.FAINT,
                                             font=theme.fpx(theme.SANS, 12))
        self.hook(lambda: self.coords(self._footer_item, self.margin(), self._size[1] - theme.S(5)))

        if self.intro:
            # Only when you arrive here: the title waits a moment (hidden by matching the panel color), then pops.
            self._title_lbl.configure(fg=theme.PANEL)
            self.after(POP_DELAY_MS, self._start_pop)

    def _start_pop(self):
        """Shows the title and plays its pop-in (unless the screen has already been replaced)."""
        try:
            if not self.winfo_exists():
                return
            self._title_lbl.configure(fg=theme.TEXT)
            pop_in(self._title_lbl, theme.SEMIBOLD, 56, px=True)
        except tk.TclError:
            pass

    def _build_hero(self, body, title, host):
        """Builds the content of the big centered panel."""
        AccentBar(body, 8).pack(fill="x")
        inner = tk.Frame(body, bg=theme.PANEL)
        inner.pack(fill="x", padx=theme.S(48), pady=(theme.S(40), theme.S(48)))

        eyebrow = tk.Frame(inner, bg=theme.PANEL)
        eyebrow.pack()
        label_font = theme.fpx(theme.SEMIBOLD, 14)
        tk.Label(eyebrow, text=text.t("Hosted By").upper() + " ", bg=theme.PANEL, fg=theme.DIM,
                 font=label_font).pack(side="left")
        tk.Label(eyebrow, text=host.upper(), bg=theme.PANEL, fg=theme.ACCENT_TEXT, font=label_font).pack(side="left")

        title_font = theme.fpx(theme.SEMIBOLD, 56)
        holder = tk.Frame(inner, bg=theme.PANEL)
        holder.pack(fill="x", pady=(theme.S(24), 0))
        self._title_lbl = tk.Label(holder, text=title.upper(), fg=theme.TEXT, bg=theme.PANEL, font=title_font,
                                   wraplength=theme.S(HERO_W - 96), justify="center")
        self._title_lbl.update_idletasks()
        holder.configure(height=self._title_lbl.winfo_reqheight())
        holder.pack_propagate(False)
        self._title_lbl.place(relx=0.5, rely=0.5, anchor="center")

        buttons = tk.Frame(inner, bg=theme.PANEL)
        buttons.pack(pady=(theme.S(40), 0))
        big = dict(height=56, pad=40, font=theme.fpx(theme.SEMIBOLD, 16))
        GlassButton(buttons, text.t("Button Start"), self._on_start, kind="primary", **big).pack(side="left")
        continue_btn = GlassButton(buttons, text.t("Button Continue"), self._on_continue, kind="secondary", **big)
        continue_btn.pack(side="left", padx=theme.S(16))
        if not has_save():
            continue_btn.configure(state="disabled")
        GlassButton(buttons, text.t("Button End"), self._on_end, kind="secondary", **big).pack(side="left")

        chips = tk.Frame(inner, bg=theme.PANEL)
        chips.pack(pady=(theme.S(32), 0))
        players = len(self.app.players)
        captains = sum(1 for p in self.app.players if p.captain)
        teams = len(self.app.teams)
        values = {"players": players, "captains": captains, "teams": teams}
        Chip(chips, "players.csv").pack(side="left")
        Chip(chips, text.t("Greeting Players", **values)).pack(side="left", padx=theme.S(8))
        Chip(chips, text.t("Greeting Captains", **values)).pack(side="left")
        Chip(chips, text.t("Greeting Teams", **values), accent=True).pack(side="left", padx=(theme.S(8), 0))

    def _hero_rect(self):
        """Centers the big panel in the space under the header row."""
        width = min(theme.S(HERO_W), self._size[0] - 2 * self.margin())
        top = self.body_top()
        bottom = self._size[1] - self.margin()
        height = self._hero_h
        return ((self._size[0] - width) // 2, top + (bottom - top - height) // 2, width, height)

    def _draw_compass(self):
        """Draws the big thin-line compass star behind the panel, in a faint color so it stays in the background."""
        import math
        for item in self._compass:
            self.delete(item)
        self._compass = []
        x, y, w, h = self._hero_rect()
        cx, cy = x + w / 2, y + h / 2
        unit = theme.S(1) * 1.6
        base = theme.mix(theme.BG, theme.AURORA[0], 0.55 if theme.MODE == "dark" else 0.65)
        pts = []
        for i in range(16):
            a = math.radians(i * 22.5 - 90)
            rad = 190 if i % 4 == 0 else (118 if i % 4 == 2 else 24)
            pts += [cx + rad * unit * math.cos(a), cy + rad * unit * math.sin(a)]
        self._compass.append(self.create_polygon(*pts, fill="", outline=base, width=1))
        for radius in (150, 186):
            r = radius * unit
            self._compass.append(self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=base, width=1))
        for item in self._compass:
            self.tag_raise(item, self._bg_item)

    # ---------- buttons ----------

    def _open_theme_picker(self):
        """Opens the window for picking a new accent color."""
        picker.open_accent_picker(self.app, self)

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
        """Closes the app (after the unsaved-changes warning)."""
        self.app.request_close()
