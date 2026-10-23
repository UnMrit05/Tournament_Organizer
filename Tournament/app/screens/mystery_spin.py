"""Screen 3 - Mystery Hero. Spins a role, then a character, for every player on every team.
The two side lists and the player card are drawn straight onto canvases, so a Confirm only touches the bits that changed."""

import random

from app.data.roster import characters_for_role
from app.data.save_manager import save_state, serialize_app_state
from app.ui import dialogs, kit, text, theme
from app.ui.player_icons import platform_photo, role_photo
from app.ui.slot_reel import SlotReel
from app.ui.stage import Stage
from app.ui.widgets import GlassButton, fit_text, line_height, text_width

ROLE_ORDER = ("Vanguard", "Duelist", "Strategist")
REEL_H = 152
POOL_H = 28
HEAD_H = 36
BOX_PAD = 8
ROW_H = 30
ROW_SIDE = 12
CARD_PAD_X = 24
CARD_PAD_Y = 12


class MysterySpinScreen(Stage):
    """The Mystery Hero page: spin for roles, then characters, one team at a time."""

    STEP = 2
    WATERMARK = "center"

    def __init__(self, parent, app):
        """Sets up the fonts, the sorted and upcoming lists, the middle spin area and the footer buttons."""
        super().__init__(parent, app, "mystery_spin")
        self.set_title(text.t("Mystery Hero Heading"))
        self.active_team = None
        self.phase = "role"        # "role" | "character" | "done"
        self.current_pick = None
        self._animating = False
        self._proceed_confirmed = False
        self._sorted_order = []    # teams in the order they finished, so the Sorted list reads top to bottom
        self._pane_sig = {"left": None, "right": None}
        self._box_y = {}           # id(team) -> (top, bottom) of its box in the Upcoming list
        self._mid_cache = (None, None)
        self._pool_entries = []
        self._phase_text = ""
        self._team_text = ""
        self._center_version = 0
        self._center_drawn = None

        self._f_head = theme.fpx(theme.SANS, 18)
        self._f_name = theme.fpx(theme.SANS, 16)
        self._f_char = theme.fpx(theme.SANS, 15)
        self._f_label = theme.fpx(theme.SEMIBOLD, 11)
        self._f_big = theme.fpx(theme.SANS, 32)
        self._f_small = theme.fpx(theme.SANS, 17)
        self._card_h = self._compute_card_h()

        self._build_sides()
        self._build_middle()
        self._build_footer()

        self._activate_team(self._pick_default_team(), reset_previous=False)
        self._refresh_meta()
        self._refresh_side_panes()

    # ---------- grid: left 3 columns, middle 6, right 3 - so the middle is exactly in the middle ----------

    def _side_w(self):
        """How wide each side list is (3 columns)."""
        return self.span_w(3)

    def _mid_w(self):
        """How wide the middle block is (6 columns)."""
        return self.span_w(6)

    def _right_x(self):
        """Where the right list starts."""
        return self.col_x(9)

    # ---------- skeleton ----------

    def _build_sides(self):
        """The Sorted list on the left and the Upcoming list on the right, each a titled panel with one scrolling canvas."""
        top = lambda: self.body_top()
        list_top = lambda: top() + theme.S(44)
        list_h = lambda: self.body_bottom() - list_top()
        teams = len(self.app.teams)
        pad = theme.S(12)

        self._sorted_section = self.section(text.t("Sorted Label", done=0, teams=teams),
                                            lambda: (self.col_x(0), top(), self._side_w()))
        left = self.draw_panel(lambda: (self.col_x(0), list_top(), self._side_w(), list_h()))
        self.left = kit.ScrollCanvas(self, theme.PANEL, on_size=lambda w: self._width_changed("left"))
        self.put(self.left, lambda: (left()[0] + pad, left()[1] + pad, left()[2] - 2 * pad, left()[3] - 2 * pad),
                 on_rect=self.left.fit)

        self.section(text.t("Upcoming Label"), lambda: (self._right_x(), top(), self._side_w()))
        right = self.draw_panel(lambda: (self._right_x(), list_top(), self._side_w(), list_h()))
        self.right = kit.ScrollCanvas(self, theme.PANEL, on_size=lambda w: self._width_changed("right"))
        self.put(self.right, lambda: (right()[0] + pad, right()[1] + pad, right()[2] - 2 * pad, right()[3] - 2 * pad),
                 on_rect=self.right.fit)
        kit.on_click(self.right.canvas, self._on_right_click)
        kit.make_hot(self.right.canvas)

    def _compute_card_h(self):
        """Works out how tall the player card is from the font sizes, so nothing has to be measured on screen."""
        s = theme.S
        body = (line_height(self._f_label) + s(2) + line_height(self._f_big) + s(4) + s(26) + s(6) + s(26))
        return 2 + s(HEAD_H) + 2 * s(CARD_PAD_Y) + body

    def _mid(self):
        """Works out the y of every piece of the middle column so the whole stack sits centered between header and footer."""
        key = (self._size, self._card_h)
        if self._mid_cache[0] == key:
            return self._mid_cache[1]
        s = theme.S
        pieces = [("title", s(36)), ("gap", s(8)), ("team", s(22)), ("gap", s(16)), ("card", self._card_h),
                  ("gap", s(16)), ("reel", s(REEL_H)), ("gap", s(16)), ("pool", s(POOL_H)),
                  ("gap", s(16)), ("acts", s(theme.FOOTER_H))]
        total = sum(h for _name, h in pieces)
        top, bottom = self.body_top(), self.body_bottom()
        y = top + max(0, (bottom - top - total) // 2)
        geo = {"cx": self.col_x(3) + self._mid_w() / 2, "x": self.col_x(3), "w": self._mid_w()}
        for name, height in pieces:
            if name != "gap":
                geo[name] = y
                geo[name + "_h"] = height
            y += height
        self._mid_cache = (key, geo)
        return geo

    def _build_middle(self):
        """The headings, the reel and the Spin / Confirm buttons. The card and the pool chips are drawn in _draw_center."""
        self._phase_item = self.create_text(0, 0, anchor="center", text="", fill=theme.TEXT,
                                            font=theme.fpx(theme.SEMIBOLD, 32))
        self._team_item = self.create_text(0, 0, anchor="center", text="", fill=theme.DIM,
                                           font=theme.fpx(theme.SANS, 18))
        self.hook(self._place_headings)
        self.hook(self._draw_center)

        self.reel = SlotReel(self, color_for=self._reel_color, icon_for=self._reel_icon)
        self.put(self.reel, lambda: (self._mid()["x"], self._mid()["reel"], self._mid()["w"], theme.S(REEL_H)))

        spin_w = theme.S(theme.BUTTON_W)
        self.spin_btn = GlassButton(self, text.t("Spin Button"), self._on_spin_click, kind="primary",
                                    width=theme.BUTTON_W)
        self.confirm_btn = GlassButton(self, text.t("Button Confirm"), self._confirm, kind="ok",
                                       width=theme.BUTTON_W)
        half_gap = self.gutter() // 2
        acts_h = theme.S(theme.FOOTER_H)
        self.put(self.spin_btn, lambda: (self._mid()["cx"] - half_gap - spin_w, self._mid()["acts"], spin_w, acts_h))
        self.put(self.confirm_btn, lambda: (self._mid()["cx"] + half_gap, self._mid()["acts"], spin_w, acts_h))

    def _place_headings(self):
        """Centers the phase heading and the team name above the player card."""
        geo = self._mid()
        room = self._mid_w()
        self.itemconfigure(self._phase_item, text=fit_text(self._phase_text, theme.fpx(theme.SEMIBOLD, 32), room))
        self.itemconfigure(self._team_item, text=fit_text(self._team_text, theme.fpx(theme.SANS, 18), room))
        self.coords(self._phase_item, geo["cx"], geo["title"] + geo["title_h"] / 2)
        self.coords(self._team_item, geo["cx"], geo["team"] + geo["team_h"] / 2)

    def _set_headings(self, phase_text, team_text):
        """Changes the two lines of heading text."""
        phase_text = phase_text.upper()
        if (phase_text, team_text) == (self._phase_text, self._team_text):
            return
        self._phase_text, self._team_text = phase_text, team_text
        self._place_headings()

    def _build_footer(self):
        """The bottom row: Home, Back and Save on the left, a note, and Proceed on the right."""
        footer_y = lambda: self.footer_top()
        h = theme.S(theme.FOOTER_H)
        back = GlassButton(self, text.t("Button Back"), self._on_previous, kind="secondary")
        save = GlassButton(self, text.t("Button Save"), self._on_save, kind="secondary")
        proceed = GlassButton(self, text.t("Proceed Button"), self._on_proceed, kind="primary")
        gap = self.gutter()
        self.put(back, lambda: (self.footer_left(), footer_y(), back.pixel_width, h))
        self.put(save, lambda: (self.footer_left() + back.pixel_width + gap, footer_y(), save.pixel_width, h))
        self.put(proceed, lambda: (self.right_edge() - proceed.pixel_width, footer_y(), proceed.pixel_width, h))
        left = lambda: self.footer_left() + back.pixel_width + save.pixel_width + 2 * gap
        self._warn_item = self.text_note(
            "", lambda: (left(), footer_y() + h // 2, self.right_edge() - proceed.pixel_width - gap - left()),
            color=theme.ACCENT_TEXT)

    def _set_warning(self, message):
        """Shows (or clears) the line of text in the footer."""
        self.set_note(self._warn_item, message)

    # ---------- sequencing ----------

    def _current_team(self):
        """Returns the team currently being spun for."""
        return self.active_team

    def _spin_order(self, team):
        """Lists a team's players in spin order, captain first."""
        return [team.captain] + [p for p in team.slots if p is not None]

    def _first_unresolved(self, team, phase):
        """Finds the first player on the team who hasn't got a role (or character) yet."""
        target = team.player_roles if phase == "role" else team.player_characters
        for p in self._spin_order(team):
            if p.ign not in target:
                return p
        return None

    def _current_player(self):
        """Returns the player who is up next, or None if there isn't one."""
        team = self.active_team
        if team is None or self.phase == "done":
            return None
        return self._first_unresolved(team, self.phase)

    def _team_fully_spun(self, team):
        """Says whether every player on the team already has a character."""
        order = self._spin_order(team)
        return all(p.ign in team.player_characters for p in order)

    def _phase_for_team(self, team):
        """Works out if the team is still on the role spin or has moved on to characters."""
        if self._first_unresolved(team, "role") is not None:
            return "role"
        return "character"

    def _pick_default_team(self):
        """Picks the first team (in draft order) that isn't fully sorted yet."""
        for team in self.app.teams:
            if not self._team_fully_spun(team):
                return team
        return None

    def _activate_team(self, team, reset_previous=True):
        """Makes this team the one being spun for, wiping the old team's spins if it was half done."""
        previous = self.active_team
        if reset_previous and previous is not None and previous is not team \
                and not self._team_fully_spun(previous):
            previous.reset_mystery()
        self.active_team = team
        self.phase = self._phase_for_team(team) if team is not None else "done"
        self.current_pick = None

    def _select_team(self, team):
        """Switches to the clicked team (unless it's already active, finished or mid-spin) and refreshes."""
        if self._animating or team is self.active_team or self._team_fully_spun(team):
            return
        self._activate_team(team)
        self._refresh_meta()
        self._refresh_side_panes()

    # ---------- spinning ----------

    def _weighted_role_options(self, team):
        """Lists the roles still left in the team's pool, one entry per spot."""
        return [r for r, cnt in team.role_pool.items() for _ in range(cnt)]

    def _character_options(self, team, role):
        """Lists characters for this role that the team hasn't used yet."""
        if not role:
            return []
        used = set(team.player_characters.values())
        return [c.name for c in characters_for_role(self.app.roster, role) if c.name not in used]

    def _current_options(self):
        """Gets whatever the reel should be choosing between right now."""
        team = self.active_team
        if team is None or self.phase == "done":
            return []
        if self.phase == "role":
            return self._weighted_role_options(team)
        player = self._current_player()
        role = team.player_roles.get(player.ign) if player else None
        return self._character_options(team, role)

    def _phase_role(self):
        """The role of the player who is up (only matters in the character phase), or None."""
        team = self.active_team
        player = self._current_player()
        if team is None or player is None:
            return None
        return team.player_roles.get(player.ign)

    def _reel_color(self, value):
        """The color a reel name is drawn in: its role color on the role spin, the player's role color on the character spin."""
        role = value if self.phase == "role" else self._phase_role()
        return theme.ROLE_TEXT.get(role) or theme.ROLE_COLOR.get(role) or theme.ACCENT_TEXT

    def _reel_icon(self, value):
        """The little role picture shown beside a role result (the character spin has none)."""
        if self.phase == "role":
            return role_photo(value, 40)
        return None

    def _on_spin_click(self):
        """Picks a random result and starts the reel spinning towards it."""
        if self._animating or self.phase == "done":
            return
        options = self._current_options()
        if not options:
            self.current_pick = None
            self.reel.set_static(text.t("No Options"))
            return
        self.current_pick = random.choice(options)
        self._animating = True
        self._set_warning("")
        self._set_controls_enabled(spin=False, confirm=False)
        self.reel.spin(options, self.current_pick, on_done=self._on_spin_done)

    def _on_spin_done(self):
        """Turns the Spin and Confirm buttons back on once the reel stops."""
        self._animating = False
        self._set_controls_enabled(spin=True, confirm=True)

    def _confirm(self):
        """Locks in the current pick for the player and moves on to the next one."""
        if self._animating:
            return
        team = self.active_team
        player = self._current_player()
        if not team or not player or self.current_pick is None:
            return
        if self.phase == "role":
            team.player_roles[player.ign] = self.current_pick
            team.role_pool[self.current_pick] -= 1
        else:
            team.player_characters[player.ign] = self.current_pick
        self.current_pick = None

        if self._team_fully_spun(team):
            self._activate_team(self._pick_default_team(), reset_previous=False)
        else:
            self.phase = self._phase_for_team(team)

        self._refresh_meta()
        self._refresh_side_panes()

    def _set_controls_enabled(self, spin=True, confirm=True):
        """Turns the Spin and Confirm buttons on or off."""
        self.spin_btn.configure(state="normal" if spin else "disabled")
        self.confirm_btn.configure(state="normal" if confirm else "disabled")

    # ---------- the middle: player card and pool chips ----------

    def _refresh_meta(self):
        """Updates the middle area: headings, player card, pool chips and the reel prompt."""
        team = self.active_team
        player = self._current_player()

        if self.phase == "done" or team is None:
            self._set_headings(text.t("All Done Heading"), text.t("All Done Text"))
            self._pool_entries = []
            self._center_version += 1
            self._draw_center()
            self.reel.set_static("")
            self._set_controls_enabled(spin=False, confirm=False)
            return

        phase_label = text.t("Role Spin Heading") if self.phase == "role" else text.t("Character Spin Heading")
        self._set_headings(phase_label, team.name)

        if self.phase == "role":
            self._pool_entries = [(f"{r} ×{c}", theme.ROLE_COLOR.get(r, theme.DIM))
                                  for r, c in list(team.role_pool.items())[:len(ROLE_ORDER)]]
        else:
            role = team.player_roles.get(player.ign, "")
            remaining = len(self._character_options(team, role))
            self._pool_entries = [(text.t("Characters Left", n=remaining, role=role), theme.ROLE_COLOR.get(role, theme.DIM))]
        self._center_version += 1
        self._draw_center()
        self.reel.set_static(text.t("Press Spin"))
        self._set_controls_enabled(spin=True, confirm=False)

    def _draw_center(self):
        """Draws the player card (or the Done box) and the pool chips. Skips the work when nothing changed since last time."""
        if self._size[0] < 10:
            return
        signature = (self._size, self._center_version)
        if signature == self._center_drawn:
            return
        self._center_drawn = signature
        self.delete("center")
        geo = self._mid()
        team = self.active_team
        if self.phase == "done" or team is None:
            self._draw_done_card(geo)
        else:
            self._draw_player_card(geo, team, self._current_player())
        self._draw_pool(geo)

    def _draw_done_card(self, geo):
        """The box shown instead of the player card once every team is sorted."""
        x, y, w, h = int(geo["x"]), int(geo["card"]), int(geo["w"]), int(self._card_h)
        kit.box(self, x, y, x + w, y + h, theme.PANEL, theme.LINE, ("center",))
        self.create_text(x + w / 2, y + h / 2, text=text.t("Done Label").upper(), fill=theme.ACCENT_TEXT,
                         font=theme.fpx(theme.SEMIBOLD, 28), tags=("center",))

    def _draw_player_card(self, geo, team, player):
        """The player info card: a colored team header, then who's up, their names, platform and roles."""
        s = theme.S
        tags = ("center",)
        ti = self.app.teams.index(team) if team in self.app.teams else 0
        h1, h2 = theme.team_hue(ti)
        bg = theme.team_body_color((h1, h2))
        x, y, w, h = int(geo["x"]), int(geo["card"]), int(geo["w"]), int(self._card_h)
        kit.box(self, x, y, x + w, y + h, bg, theme.mix(theme.BASE, h1, 0.60), tags)

        head_h = s(HEAD_H)
        kit.draw_gradient(self, x + 1, y + 1, w - 2, head_h, h1, h2, True, tags)
        pad = s(12)
        right_font = theme.fpx(theme.SANS, 16)
        right_text = text.t("Captain Of", name=team.captain.twitch)
        side = min(text_width(right_font, right_text), (w - 2 * pad) // 2)
        self.create_text(x + w - 1 - pad, y + 1 + head_h / 2, text=fit_text(right_text, right_font, side), anchor="e",
                         fill=theme.HEADER_INK, font=right_font, tags=tags)
        room = w - 2 * pad - side - s(12)
        self.create_text(x + 1 + pad, y + 1 + head_h / 2, text=fit_text(team.name, self._f_head, room), anchor="w",
                         fill=theme.HEADER_INK, font=self._f_head, tags=tags)

        order = self._spin_order(team)
        left = x + 1 + s(CARD_PAD_X)
        inner_w = w - 2 - 2 * s(CARD_PAD_X)
        cy = y + 1 + head_h + s(CARD_PAD_Y)
        label = text.t("Player Progress", n=order.index(player) + 1, total=len(order)).upper()
        self.create_text(left, cy, text=fit_text(label, self._f_label, inner_w), anchor="nw", fill=theme.DIM,
                         font=self._f_label, tags=tags)
        cy += line_height(self._f_label) + s(2)
        self.create_text(left, cy, text=fit_text(player.twitch, self._f_big, inner_w), anchor="nw", fill=theme.TEXT,
                         font=self._f_big, tags=tags)
        cy += line_height(self._f_big) + s(4)

        mid = cy + s(26) / 2
        px = left
        for piece in (text.t("In Game", ign=player.ign), text.t("Peak", rank=player.peak_rank)):
            shown = fit_text(piece, self._f_small, left + inner_w - px)
            self.create_text(px, mid, text=shown, anchor="w", fill=theme.DIM, font=self._f_small, tags=tags)
            px += text_width(self._f_small, shown) + s(16)
        photo = platform_photo(player.platform, 20) if player.platform else None
        if photo is not None and px + s(20) + s(8) + text_width(self._f_small, player.platform) <= left + inner_w:
            self.create_image(px, mid, image=photo, anchor="w", tags=tags)
            self.create_text(px + s(20) + s(8), mid, text=player.platform, anchor="w", fill=theme.DIM,
                             font=self._f_small, tags=tags)
        cy += s(26) + s(6)

        self._draw_role_line(left, cy + s(26) / 2, left + inner_w, team, player, bg, tags)

    def _draw_role_line(self, x, mid, limit, team, player, bg, tags):
        """The 'Role ... Prefers ...' line of the card for the player who is up. Stops drawing before it would run out of room."""
        s = theme.S

        def label(txt, px):
            """Draws a plain word and gives back where the next thing starts."""
            self.create_text(px, mid, text=txt, anchor="w", fill=theme.DIM, font=self._f_small, tags=tags)
            return px + text_width(self._f_small, txt) + s(8)

        def role(name, px):
            """Draws a role badge and its name, or gives back None when it wouldn't fit."""
            badge = kit.badge_side(18)
            width = badge + s(6) + text_width(self._f_small, name)
            if px + width > limit:
                return None
            kit.draw_role_badge(self, px, mid - badge / 2, name, 18, bg, tags)
            self.create_text(px + badge + s(6), mid, text=name, anchor="w", fill=theme.ROLE_TEXT.get(name, theme.DIM),
                             font=self._f_small, tags=tags)
            return px + width + s(10)

        if self.phase == "character":
            assigned = team.player_roles.get(player.ign)
            x = label(text.t("Role Label"), x)
            if assigned:
                x = role(assigned, x) or x
            x += s(8)
        x = label(text.t("Prefers"), x)
        for name in player.preferred_roles:
            nxt = role(name, x)
            if nxt is None:
                break
            x = nxt

    def _draw_pool(self, geo):
        """Draws the pool chips in one centered row (they sit under the reel)."""
        if not self._pool_entries:
            return
        font = theme.fpx(theme.SANS, 15)
        gap = theme.S(8)
        widths = [kit.chip_width(label, font, True) for label, _color in self._pool_entries]
        total = sum(widths) + gap * (len(widths) - 1)
        x = geo["cx"] - total / 2
        for (label, color), width in zip(self._pool_entries, widths):
            kit.draw_chip(self, int(x), int(geo["pool"]), label, font, theme.mix(theme.BTN_TOP, theme.BTN_BOTTOM, 0.5),
                          theme.BTN_EDGE, theme.TEXT, dot=color, tags=("center",), height=theme.S(POOL_H))
            x += width + gap

    # ---------- the side lists ----------

    def _width_changed(self, which):
        """A side list got a new width, so its boxes have to be drawn again at that width."""
        self._pane_sig[which] = None
        self._draw_pane(which)

    def _pane_teams(self, which):
        """The teams that belong in a list: finished ones (in the order they finished) on the left, the rest on the right."""
        if which == "left":
            return list(self._sorted_order)
        return [t for t in self.app.teams if not self._team_fully_spun(t)]

    def _signature(self, which):
        """Boils down everything a list shows (teams, highlight, roles, characters) so we can tell when it needs redrawing."""
        rows = []
        for team in self._pane_teams(which):
            rows.append((id(team), tuple((p.ign, team.player_roles.get(p.ign), team.player_characters.get(p.ign))
                                         for p in self._spin_order(team))))
        active = id(self.active_team) if which == "right" and self.active_team is not None else None
        return (tuple(rows), active)

    def _refresh_side_panes(self):
        """Redraws whichever list actually changed and updates the 'Sorted' count."""
        for team in self.app.teams:
            if self._team_fully_spun(team) and team not in self._sorted_order:
                self._sorted_order.append(team)
        for which in ("left", "right"):
            self._draw_pane(which)
        label = text.t("Sorted Label", done=len(self._sorted_order), teams=len(self.app.teams))
        if label != self._sorted_section["label"]:
            self._sorted_section["label"] = label
            self.relayout()
        self._show_active_box()

    def _draw_pane(self, which):
        """Draws one side list from scratch on its canvas - unless nothing it shows has changed."""
        pane = self.left if which == "left" else self.right
        width = pane.width
        if width < 40:
            return
        signature = self._signature(which)
        if signature == self._pane_sig[which]:
            return
        self._pane_sig[which] = signature
        cv = pane.canvas
        cv.delete("all")
        gap = theme.S(theme.GUTTER)
        y = 0
        teams = self._pane_teams(which)
        if which == "right":
            self._box_y = {}
        for team in teams:
            height = self._draw_team_box(cv, team, 0, y, width, which)
            if which == "right":
                self._box_y[id(team)] = (y, y + height)
            y += height + gap
        pane.set_content_height(max(0, y - gap))
        if which == "left" and not teams:
            cv.create_text(width / 2, max(40, pane.height / 2), text=text.t("Sorted Empty"), fill=theme.FAINT,
                           font=theme.FONT_NOTE, width=min(width - theme.S(24), theme.S(220)), justify="center")

    def _show_active_box(self):
        """Scrolls the Upcoming list so the active team's box is in view."""
        top_bottom = self._box_y.get(id(self.active_team)) if self.active_team is not None else None
        if top_bottom is not None:
            self.right.ensure_visible(*top_bottom)

    def _draw_team_box(self, cv, team, x, y, w, which):
        """Draws one team's box: a colored header and a row per player. Gives back the box's height."""
        s = theme.S
        ti = self.app.teams.index(team)
        h1, h2 = theme.team_hue(ti)
        bg = theme.team_body_color((h1, h2))
        active = which == "right" and team is self.active_team
        order = self._spin_order(team)
        head_h = s(HEAD_H)
        height = 2 + head_h + 2 * s(BOX_PAD) + len(order) * s(ROW_H)
        tags = ("hot", f"team:{ti}") if which == "right" else ()
        border = 2 if active else 1
        edge = theme.ACCENT_TEXT if active else theme.mix(theme.BASE, h1, 0.60)
        cv.create_rectangle(x, y, x + w, y + height, fill=edge, outline="", tags=tags)
        cv.create_rectangle(x + border, y + border, x + w - border, y + height - border, fill=bg, outline="", tags=tags)
        kit.draw_gradient(cv, x + 1, y + 1, w - 2, head_h, h1, h2, True, tags)
        pad = s(12)
        cv.create_text(x + 1 + pad, y + 1 + head_h / 2, text=fit_text(team.name, self._f_head, w - 2 - 2 * pad),
                       anchor="w", fill=theme.HEADER_INK, font=self._f_head, tags=tags)
        row_y = y + 1 + head_h + s(BOX_PAD)
        for player in order:
            self._draw_row(cv, team, player, x + 1 + s(ROW_SIDE), x + w - 1 - s(ROW_SIDE), row_y + s(ROW_H) / 2,
                           bg, tags)
            row_y += s(ROW_H)
        return height

    def _draw_row(self, cv, team, player, x0, x1, ymid, bg, tags):
        """One player's row: name (left-aligned) with the C right after it for the captain, then the character
        and the role icon, which are pushed against the right edge so every icon lines up in one column."""
        s = theme.S
        role = team.player_roles.get(player.ign)
        char = team.player_characters.get(player.ign, "")
        if role:
            side = kit.badge_side(18)
            kit.draw_role_badge(cv, x1 - side, ymid - side / 2, role, 18, bg, tags)
            icons_w = side
        else:
            roles = [r for r in player.preferred_roles if r]
            side = kit.badge_side(14)
            gap = s(4)
            icons_w = len(roles) * side + max(0, len(roles) - 1) * gap
            rx = x1 - icons_w
            for name in roles:
                kit.draw_role_badge(cv, rx, ymid - side / 2, name, 14, bg, tags)
                rx += side + gap
        right = x1 - icons_w - (s(8) if icons_w else 0)
        avail = right - x0
        c_side = s(18)
        c_room = c_side + s(8) if player is team.captain else 0
        name_w = text_width(self._f_name, player.twitch) + c_room
        char_w = text_width(self._f_char, char) if char else 0
        spare = s(12) if char else 0
        name_room, char_room = name_w, char_w
        if name_w + spare + char_w > avail:
            # Not enough room for both: the one that is already short keeps all it needs, the other gets the rest.
            if char_w > avail * 0.55 and name_w <= avail * 0.45:
                char_room = avail - name_w - spare
            elif name_w > avail * 0.45 and char_w <= avail * 0.55:
                name_room = avail - char_w - spare
            else:
                name_room, char_room = avail * 0.45, avail * 0.55 - spare
        if char:
            cv.create_text(right, ymid, text=fit_text(char, self._f_char, int(char_room)), anchor="e",
                           fill=theme.TEXT, font=self._f_char, tags=tags)
        shown_name = fit_text(player.twitch, self._f_name, int(name_room - c_room))
        cv.create_text(x0, ymid, text=shown_name, anchor="w", fill=theme.TEXT, font=self._f_name, tags=tags)
        if player is team.captain:
            cx = x0 + text_width(self._f_name, shown_name) + s(8)
            kit.box(cv, cx, ymid - c_side / 2, cx + c_side, ymid + c_side / 2, theme.ACCENT, theme.ACCENT_EDGE, tags)
            cv.create_text(cx + c_side / 2, ymid, text="C", fill=theme.ACCENT_INK, font=theme.FONT_STEP, tags=tags)

    def _on_right_click(self, tags, event):
        """Clicking anywhere on a team box in the Upcoming list makes that team the active one."""
        for tag in tags:
            if tag.startswith("team:"):
                self._select_team(self.app.teams[int(tag[5:])])
                return

    # ---------- footer actions ----------

    def _on_previous(self):
        """Back button: wipes all spins and goes back to Tournament Type."""
        if self._animating:
            return
        for t in self.app.teams:
            t.reset_mystery()
        self.app.show_screen("tournament_type")

    def _on_save(self):
        """Saves the tournament as it is right now and says so."""
        save_state(serialize_app_state(self.app), status="Spin")
        self._set_warning("")
        dialogs.notify_saved(self.app)

    def _on_proceed(self):
        """Goes on to Bracket Settings, warning once first if anyone isn't confirmed."""
        if self._animating:
            return
        incomplete = [t for t in self.app.teams
                      if len(t.player_characters) < len(self._spin_order(t))]
        if incomplete and not self._proceed_confirmed:
            self._set_warning(text.t("Spin Not Confirmed"))
            self._proceed_confirmed = True
            return
        self._proceed_confirmed = False
        # Remember we came from Mystery Hero, so Bracket Settings' Back
        # button returns here instead of to Tournament Type.
        self.app.bracket_settings_origin = "mystery_spin"
        self.app.show_screen("bracket_settings")

    # ---------- hand-over for a light/dark switch ----------

    def is_busy(self):
        """True while the reel is spinning, so the light/dark switch waits."""
        return self._animating

    def capture_state(self):
        """Remembers which team is up, any result that hasn't been confirmed yet, the sorted order and the scroll spots."""
        teams = self.app.teams
        index = teams.index(self.active_team) if self.active_team in teams else None
        return {"team": index, "pick": self.current_pick, "proceed": self._proceed_confirmed,
                "sorted": [teams.index(t) for t in self._sorted_order if t in teams],
                "left": self.left.canvas.yview()[0], "right": self.right.canvas.yview()[0]}

    def restore_state(self, state):
        """Puts the same team up again, and shows the unconfirmed result if there was one."""
        index = state.get("team")
        teams = self.app.teams
        self._sorted_order = [teams[i] for i in state.get("sorted", []) if 0 <= i < len(teams)]
        if index is not None and 0 <= index < len(teams):
            self.active_team = teams[index]
            self.phase = self._phase_for_team(self.active_team)
        else:
            self.active_team, self.phase = None, "done"
        self.current_pick = state.get("pick")
        self._proceed_confirmed = state.get("proceed", False)
        self._refresh_meta()
        self._pane_sig = {"left": None, "right": None}
        self._refresh_side_panes()
        self.left.canvas.yview_moveto(state.get("left", 0))
        self.right.canvas.yview_moveto(state.get("right", 0))
        if self.current_pick is not None and self.phase != "done":
            self.reel.set_static(self.current_pick, self._reel_color(self.current_pick))
            self._set_controls_enabled(spin=True, confirm=True)
