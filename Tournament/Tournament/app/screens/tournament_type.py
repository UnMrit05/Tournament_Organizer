"""The tournament type screen: choose Mystery Hero (spin for roles/characters) or Normal (straight to bracket settings)."""

import tkinter as tk

from app.ui import gfx, text, theme
from app.ui.stage import Stage
from app.ui.widgets import Chip, GlassButton, HeaderBar, Panel

ART_H = 184


class TournamentTypeScreen(Stage):
    """Screen with the Mystery Hero and Normal cards and the Back button."""

    STEP = 1
    WATERMARK = "center"

    def __init__(self, parent, app):
        """Builds the title, the two big option cards and the Back button."""
        super().__init__(parent, app, "tournament_type")
        self.set_title(text.t("Tournament Type Heading"))

        self._cards = []
        mystery = self._build_card(text.t("Mystery Hero Name"), text.t("Mystery Hero Description"),
                                   text.t("Mystery Hero Chip"), (theme.ACCENT, theme.ACCENT), True,
                                   self._draw_reels, self._pick_mystery)
        normal = self._build_card(text.t("Normal Name"), text.t("Normal Description"),
                                  text.t("Normal Chip"), theme.team_hue(1), False,
                                  self._draw_bracket, self._pick_normal)
        self.put(mystery, lambda: self._card_rect(1))
        self.put(normal, lambda: self._card_rect(6))

        back = GlassButton(self, text.t("Button Back"), lambda: app.show_screen("seeding"), kind="secondary")
        self.put(back, lambda: (self.footer_left(), self.footer_top(), back.pixel_width, back.pixel_height))

    def _card_rect(self, col):
        """Where a card goes: 5 columns wide, centered between the header and the footer."""
        height = self._card_h
        top = self.body_top()
        bottom = self.body_bottom()
        return (self.col_x(col), top + (bottom - top - height) // 2, self.span_w(5), height)

    def _build_card(self, name, description, chip_text, hues, accent_chip, draw_art, command):
        """Builds one option card: color bar, artwork, name, description and a 'Choose' line."""
        h1, h2 = hues
        panel = Panel(self, stripe=False)
        body = panel.body
        HeaderBar(body, h1, h2, height=8, text="", dust=False).pack(fill="x")
        art = tk.Canvas(body, height=theme.S(ART_H), highlightthickness=0, bd=0, bg=theme.BASE)
        art.pack(fill="x")
        art.bind("<Configure>", lambda e, c=art, a=h1, b=h2, d=draw_art: self._paint_art(c, a, b, d))
        info = tk.Frame(body, bg=theme.PANEL)
        info.pack(fill="both", expand=True, padx=theme.S(24), pady=theme.S(24))
        tk.Label(info, text=name.upper(), bg=theme.PANEL, fg=theme.TEXT, font=theme.fpx(theme.SEMIBOLD, 28),
                 anchor="w").pack(fill="x")
        tk.Label(info, text=description, bg=theme.PANEL, fg=theme.DIM, font=theme.fpx(theme.SANS, 19),
                 anchor="w", justify="left", wraplength=theme.S(420)).pack(fill="x", pady=(theme.S(8), 0))
        row = tk.Frame(info, bg=theme.PANEL)
        row.pack(fill="x", pady=(theme.S(16), 0))
        Chip(row, chip_text, accent=accent_chip).pack(side="left")
        arrow = gfx.icon_image("arrow", theme.S(14), theme.ACCENT_TEXT, theme.PANEL)
        go = tk.Label(row, text=text.t("Choose").upper() + " ", bg=theme.PANEL, fg=theme.ACCENT_TEXT,
                      font=theme.fpx(theme.SEMIBOLD, 12), image=arrow or "", compound="right")
        go._arrow = arrow
        go.pack(side="right")
        panel.update_idletasks()
        self._card_h = max(getattr(self, "_card_h", 0), panel.winfo_reqheight())
        self._cards.append(panel)
        self._wire_card(panel, command)
        return panel

    def _wire_card(self, panel, command):
        """Makes the whole card clickable, with an accent border while the mouse is over it."""
        def walk(widget):
            """Binds the click on this widget and everything inside it."""
            widget.bind("<Button-1>", lambda e: command(), add="+")
            widget.bind("<Enter>", lambda e: panel.configure(bg=theme.ACCENT_TEXT), add="+")
            widget.bind("<Leave>", lambda e: panel.configure(bg=theme.LINE), add="+")
            widget.configure(cursor="hand2")
            for child in widget.winfo_children():
                walk(child)
        walk(panel)

    def _paint_art(self, canvas, c1, c2, draw_art):
        """Fills the artwork area with a soft color wash and draws the picture on it."""
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 4:
            return
        canvas.delete("all")
        top = theme.mix(theme.BASE, c1, 0.26)
        bottom = theme.mix(theme.BASE, c2, 0.08)
        img = gfx.vertical_swatch(w, h, [(0, top), (1, bottom)])
        if img is not None:
            canvas._wash = img
            canvas.create_image(0, 0, image=img, anchor="nw")
        else:
            canvas.configure(bg=top)
        draw_art(canvas, w, h)

    def _draw_reels(self, canvas, w, h):
        """Three little slot-machine reels, one per role, for the Mystery Hero card."""
        reel_w, reel_h, gap = theme.S(80), theme.S(120), theme.S(16)
        total = 3 * reel_w + 2 * gap
        x0 = (w - total) // 2
        y0 = (h - reel_h) // 2
        small = theme.fpx(theme.SEMIBOLD, 14)
        for i, role in enumerate(("Vanguard", "Duelist", "Strategist")):
            x = x0 + i * (reel_w + gap)
            canvas.create_rectangle(x, y0, x + reel_w, y0 + reel_h, fill=theme.PANEL_2, outline=theme.LINE)
            canvas.create_text(x + reel_w / 2, y0 + theme.S(16), text="?", fill=theme.FAINT, font=small)
            canvas.create_text(x + reel_w / 2, y0 + reel_h - theme.S(16), text="?", fill=theme.FAINT, font=small)
            side = theme.S(44)
            color = theme.ROLE_COLOR[role]
            cx, cy = x + reel_w / 2, y0 + reel_h / 2
            canvas.create_rectangle(cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2,
                                    fill=theme.mix(theme.PANEL_2, color, 0.2), outline=theme.mix(theme.PANEL_2, color, 0.7))
            self._draw_role_glyph(canvas, role, cx, cy, theme.S(22), color)

    @staticmethod
    def _draw_role_glyph(canvas, role, cx, cy, size, color):
        """Draws a simple shield, crossed swords or plus sign for a role."""
        r = size / 2
        if role == "Vanguard":
            canvas.create_polygon(cx, cy - r, cx + r * 0.85, cy - r * 0.55, cx + r * 0.85, cy + r * 0.1,
                                  cx, cy + r, cx - r * 0.85, cy + r * 0.1, cx - r * 0.85, cy - r * 0.55,
                                  outline=color, fill="", width=2)
        elif role == "Duelist":
            canvas.create_line(cx - r * 0.8, cy - r * 0.8, cx + r * 0.4, cy + r * 0.4, fill=color, width=2)
            canvas.create_line(cx + r * 0.8, cy - r * 0.8, cx - r * 0.4, cy + r * 0.4, fill=color, width=2)
            canvas.create_line(cx + r * 0.2, cy + r * 0.7, cx + r * 0.7, cy + r * 0.2, fill=color, width=2)
            canvas.create_line(cx - r * 0.2, cy + r * 0.7, cx - r * 0.7, cy + r * 0.2, fill=color, width=2)
        else:
            canvas.create_line(cx, cy - r * 0.8, cx, cy + r * 0.8, fill=color, width=3)
            canvas.create_line(cx - r * 0.8, cy, cx + r * 0.8, cy, fill=color, width=3)

    def _draw_bracket(self, canvas, w, h):
        """A tiny bracket diagram for the Normal card."""
        u = theme.S(1)
        ox, oy = (w - 248 * u) / 2, (h - 112 * u) / 2
        edge = theme.DIM

        def box(x, y, bw, bh, fill=theme.PANEL_2, outline=edge, width=1):
            """Draws one team box."""
            canvas.create_rectangle(ox + x * u, oy + y * u, ox + (x + bw) * u, oy + (y + bh) * u,
                                    fill=fill, outline=outline, width=width)

        for y in (4, 32, 60, 88):
            box(0, y, 64, 20)
        box(104, 18, 64, 20)
        box(104, 74, 64, 20)
        box(208, 46, 40, 20, fill=theme.mix(theme.BASE, theme.team_hue(1)[0], 0.4), outline=theme.TEXT)
        for pts in ([(64, 14), (84, 14), (84, 28), (104, 28)], [(64, 42), (84, 42), (84, 28)],
                    [(64, 70), (84, 70), (84, 84), (104, 84)], [(64, 98), (84, 98), (84, 84)],
                    [(168, 28), (188, 28), (188, 56), (208, 56)], [(168, 84), (188, 84), (188, 56)]):
            flat = [c for x, y in pts for c in (ox + x * u, oy + y * u)]
            canvas.create_line(*flat, fill=edge)

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
