"""The Congratulations screen: shows the winning team, its captain and roster once there's a champion."""

import tkinter as tk

from app.ui import gfx, kit, text, theme
from app.ui.pop_anim import pop_in_item
from app.ui.stage import POP_DELAY_MS, Stage
from app.ui.widgets import GlassButton, fit_text, line_height, text_width

TILE_W = 296
TILE_H = 76
MEDAL = 96
COLUMNS = 3


class CongratsScreen(Stage):
    """Screen that shows who won the tournament."""

    STEP = 5
    WATERMARK = "center"

    def __init__(self, parent, app):
        """Builds the burst, the trophy medal, the heading, the winner line, the roster tiles and the Back and End buttons."""
        super().__init__(parent, app, "congrats")
        self.champion = getattr(app.bracket, "champion", None) if app.bracket else None
        self._burst_item = None
        self._burst_img = None
        self._medal_items = []
        self._medal_imgs = []

        self._heading = self.create_text(0, 0, anchor="center", text=text.t("Congratulations Heading").upper(),
                                         fill=theme.TEXT, font=theme.fpx(theme.SEMIBOLD, 64))
        self._winner = self.create_text(0, 0, anchor="center", text="", fill=theme.ACCENT_TEXT,
                                        font=theme.fpx(theme.SANS, 34))
        self._players = []
        self._drawn_for = None
        if self.champion is None:
            self.itemconfigure(self._winner, text=text.t("No Champion Text"), fill=theme.DIM)
        else:
            self.itemconfigure(self._winner, text=text.t("Winner Line", team=self.champion.name))
            self._players = self.champion.all_players()

        self.hook(self._draw_stage)
        self.hook(self._draw_roster)
        self._build_footer()
        if self.intro:
            # Only when you arrive here: wait a moment, then pop. A color or window-size change never replays it.
            self.itemconfigure(self._heading, state="hidden")
            self.after(POP_DELAY_MS, self._start_pop)

    def _start_pop(self):
        """Shows the heading and plays its pop-in (unless the screen has already been replaced)."""
        try:
            if not self.winfo_exists():
                return
            self.itemconfigure(self._heading, state="normal")
            pop_in_item(self, self._heading, theme.SEMIBOLD, 64)
        except tk.TclError:
            pass

    # ---------- layout ----------

    def _stack(self):
        """Works out where each piece of the centered column goes: medal, heading, winner line and the roster rows."""
        s = theme.S
        rows = (len(self._players) + COLUMNS - 1) // COLUMNS
        roster_h = rows * s(TILE_H) + max(0, rows - 1) * self.gutter()
        pieces = [("medal", s(MEDAL)), ("gap", s(16)), ("heading", s(64)), ("gap", s(8)), ("winner", s(38))]
        if rows:
            pieces += [("gap", s(24)), ("roster", roster_h)]
        total = sum(h for _name, h in pieces)
        top, bottom = self.body_top(), self.body_bottom()
        y = top + max(0, (bottom - top - total) // 2)
        geo = {"cx": self._size[0] / 2}
        for name, height in pieces:
            if name != "gap":
                geo[name] = y
                geo[name + "_h"] = height
            y += height
        return geo

    def _draw_stage(self):
        """Positions the heading, the winner line, the medal and the burst of rays behind everything."""
        geo = self._stack()
        cx = geo["cx"]
        room = self._size[0] - 2 * self.margin()
        self.coords(self._heading, cx, geo["heading"] + geo["heading_h"] / 2)
        self.coords(self._winner, cx, geo["winner"] + geo["winner_h"] / 2)
        text_now = self.itemcget(self._winner, "text")
        self.itemconfigure(self._winner, text=fit_text(text_now, theme.fpx(theme.SANS, 34), room))
        self._place_medal(cx, geo["medal"])
        self._place_burst(cx, geo["medal"] + geo["medal_h"] / 2)

    def _place_burst(self, cx, cy):
        """Puts the faint rays behind the medal."""
        size = theme.S(1000)
        if self._burst_item is None:
            img = gfx.burst(size, theme.ACCENT)
            if img is None:
                return
            self._burst_img = img
            self._burst_item = self.create_image(cx, cy, image=img)
            self.tag_raise(self._burst_item, self._bg_item)
        self.coords(self._burst_item, cx, cy)

    def _place_medal(self, cx, top):
        """Draws the square accent medal with the trophy on it, once, then just moves it."""
        side = theme.S(MEDAL)
        if not self._medal_items:
            face = gfx.vertical_swatch(side, side, [(0, theme.ACCENT_HI), (0.52, theme.ACCENT), (1, theme.ACCENT_LO)])
            icon = gfx.icon_alpha("trophy", theme.S(56), theme.ACCENT_INK)
            self._medal_imgs = [face, icon]
            if face is not None:
                self._medal_items.append(self.create_image(0, 0, anchor="nw", image=face))
            else:
                self._medal_items.append(self.create_rectangle(0, 0, side, side, fill=theme.ACCENT, outline=""))
            self._medal_items.append(self.create_rectangle(0, 0, side, side, outline=theme.ACCENT_LO))
            if icon is not None:
                self._medal_items.append(self.create_image(0, 0, image=icon))
        left = cx - side / 2
        box, edge = self._medal_items[0], self._medal_items[1]
        if self.type(box) == "image":
            self.coords(box, left, top)
        else:
            self.coords(box, left, top, left + side, top + side)
        self.coords(edge, left, top, left + side - 1, top + side - 1)
        if len(self._medal_items) > 2:
            self.coords(self._medal_items[2], cx, top + side / 2)

    # ---------- roster ----------

    def _team_index(self, team):
        """Where the team sits in the draft order (decides its color)."""
        for i, t in enumerate(self.app.teams):
            if t is team:
                return i
        return 0

    def _tile_rect(self, index, geo):
        """Where tile number `index` goes on the 3-column roster grid, centered under the heading."""
        gap = self.gutter()
        avail = self._size[0] - 2 * self.margin()
        width = min(theme.S(TILE_W), (avail - (COLUMNS - 1) * gap) // COLUMNS)
        height = theme.S(TILE_H)
        row, col = divmod(index, COLUMNS)
        in_row = min(COLUMNS, len(self._players) - row * COLUMNS)
        total = in_row * width + (in_row - 1) * gap
        return (int(geo["cx"] - total / 2 + col * (width + gap)), int(geo["roster"] + row * (height + gap)),
                int(width), int(height))

    def _draw_roster(self):
        """Draws one tile per player on the winning team (captain first), straight on the canvas.
        It only redraws when the window size changes."""
        if not self._players or self._size[0] < 10:
            return
        if self._drawn_for == self._size:
            return
        self._drawn_for = self._size
        self.delete("tile")
        geo = self._stack()
        team = self.champion
        h1, _h2 = theme.team_hue(self._team_index(team))
        for index, player in enumerate(self._players):
            self._draw_tile(team, player, h1, *self._tile_rect(index, geo))

    def _draw_tile(self, team, player, h1, x, y, w, h):
        """One player's tile. In a Mystery Hero tournament it shows the class icon of the character the player was
        given, with that character's name under the player's name. Otherwise it shows the player's preferred role
        icons and leaves the line under the name empty."""
        s = theme.S
        tags = ("tile",)
        is_captain = player is team.captain
        bg = theme.mix(theme.BASE, h1, 0.28 if theme.MODE == "dark" else 0.16)
        edge = theme.ACCENT_TEXT if is_captain else theme.mix(theme.BASE, h1, 0.60)
        border = 2 if is_captain else 1
        self.create_rectangle(x, y, x + w, y + h, fill=edge, outline="", tags=tags)
        self.create_rectangle(x + border, y + border, x + w - border, y + h - border, fill=bg, outline="", tags=tags)

        mystery = getattr(self.app, "tournament_type", None) == "mystery"
        role = team.player_roles.get(player.ign) if mystery else None
        char = team.player_characters.get(player.ign) if mystery else None
        mid = y + h / 2
        left = x + border + s(16)
        if role:
            side = kit.draw_role_badge(self, left, mid - kit.badge_side(30) / 2, role, 30, bg, tags)
            left += side + s(12)
        else:
            size, gap = 24, s(4)
            side = kit.badge_side(size)
            for name in [r for r in player.preferred_roles if r]:
                kit.draw_role_badge(self, left, mid - side / 2, name, size, bg, tags)
                left += side + gap
            left += s(12) - gap
        right = x + w - border - s(12)

        name_font = theme.fpx(theme.SANS, 21)
        small = theme.fpx(theme.SANS, 16)
        name_h = line_height(name_font)
        block = name_h + ((s(4) + line_height(small)) if char else 0)
        top = mid - block / 2
        name = player.twitch or player.ign
        extra = 0
        plat_w = kit.platform_width(player.platform, 16)
        if plat_w:
            extra += s(8) + plat_w
        tag_font = theme.fpx(theme.SEMIBOLD, 10)
        tag_text = text.t("Captain Tag").upper()
        tag_w = text_width(tag_font, tag_text) + 2 * s(6)
        if is_captain:
            extra += s(8) + tag_w
        shown = fit_text(name, name_font, right - left - extra)
        self.create_text(left, top + name_h / 2, text=shown, anchor="w", fill=theme.TEXT, font=name_font, tags=tags)
        px = left + text_width(name_font, shown)
        if plat_w:
            px += s(8)
            px += kit.draw_platform(self, px, top + name_h / 2 - s(16) / 2, player.platform, 16, tags)
        if is_captain:
            px += s(8)
            tag_h = line_height(tag_font) + 2 * s(1)
            self.create_rectangle(px, top + name_h / 2 - tag_h / 2, px + tag_w, top + name_h / 2 + tag_h / 2,
                                  fill=theme.ACCENT, outline="", tags=tags)
            self.create_text(px + tag_w / 2, top + name_h / 2, text=tag_text, fill=theme.ACCENT_INK, font=tag_font,
                             tags=tags)
        if char:
            self.create_text(left, top + name_h + s(4) + line_height(small) / 2, text=fit_text(char, small, right - left),
                             anchor="w", fill=theme.DIM, font=small, tags=tags)

    # ---------- footer ----------

    def _build_footer(self):
        """The bottom row: Back to the bracket on the left, End (after the unsaved-changes warning) on the right."""
        footer_y = lambda: self.footer_top()
        h = theme.S(theme.FOOTER_H)
        back = GlassButton(self, text.t("Button Back"), lambda: self.app.show_screen("bracket"), kind="secondary")
        end = GlassButton(self, text.t("Button End"), self.app.request_close, kind="primary")
        self.put(back, lambda: (self.footer_left(), footer_y(), back.pixel_width, h))
        self.put(end, lambda: (self.right_edge() - end.pixel_width, footer_y(), end.pixel_width, h))
