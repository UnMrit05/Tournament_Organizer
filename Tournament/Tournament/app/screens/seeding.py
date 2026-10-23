"""The drafting screen: pick players for each team's open slots from the pool on the right.
Both lists are drawn straight onto two canvases, so the screen opens in one go and nothing flickers when you click."""

import tkinter as tk

from app.data.ranks import RANK_TIERS, matches_tier, rank_sort_key, strip_subdivision
from app.data.save_manager import save_state, serialize_app_state
from app.data.team import next_open_slot
from app.ui import dialogs, gfx, kit, text, theme
from app.ui.stage import Stage
from app.ui.widgets import GlassButton, fit_text, line_height, text_width

TIER_OPTIONS = ["Any"] + RANK_TIERS

HEADER_H = 40
CARD_PAD = 12
CAP_H = 46
SLOT_H = 38
ROW_GAP = 4
NUM_SIDE = 24
DROP_W = 120
DROP_H = 28
ROSTER_H = 58
ROSTER_GAP = 8


class SeedingScreen(Stage):
    """Drafting screen with the teams on the left and the undrafted players on the right."""

    STEP = 0
    WATERMARK = "left"

    def __init__(self, parent, app):
        """Sets up the whole screen: the two canvases for the team cards and the roster, the search box and the bottom buttons."""
        super().__init__(parent, app, "seeding")
        self.set_title(text.t("Drafting Heading"))
        self.active = None            # (team_index, slot_index) or None
        self._lock_confirmed = False
        self._slot_refs = {}          # (ti, si) -> the canvas items of that slot row
        self._roster_refs = []        # one entry per non-captain player, drawn once
        self._roster_order = []
        self._head_refs = {}          # ti -> pieces of the team header (for renaming)
        self._card_y = {}             # ti -> (top, bottom) of the card on the canvas
        self._rename = None
        self._selectable_drawn = None
        self._shown_count = None
        self._undrafted = 0
        self._menu = kit.DropMenu()

        self._fonts = {"name": theme.FONT_NAME, "sub": theme.fpx(theme.SANS, 13), "small": theme.FONT_SMALL}

        self._build_teams_side()
        self._build_roster_side()
        self._build_footer()

    # ---------- screen skeleton ----------

    def _build_teams_side(self):
        """The left side: the Teams title and a panel holding the scrolling team cards."""
        top = lambda: self.body_top()
        self.section(text.t("Drafting Teams Label"), lambda: (self.col_x(0), top(), self.span_w(8)))
        panel = self.draw_panel(lambda: (self.col_x(0), top() + theme.S(44), self.span_w(8),
                                         self.body_bottom() - top() - theme.S(44)))
        self.left = kit.ScrollCanvas(self, theme.PANEL, on_size=self._on_left_size)
        pad = theme.S(12)
        self.put(self.left, lambda: (panel()[0] + pad, panel()[1] + pad, panel()[2] - 2 * pad, panel()[3] - 2 * pad),
                 on_rect=self.left.fit)
        kit.on_click(self.left.canvas, self._on_left_click)
        kit.make_hot(self.left.canvas)

    def _build_roster_side(self):
        """The right side: the roster title and a panel with the search box, the note line and the player list."""
        top = lambda: self.body_top()
        self.section(text.t("Drafting Roster Label"), lambda: (self.col_x(8), top(), self.span_w(4)))
        panel = self.draw_panel(lambda: (self.col_x(8), top() + theme.S(44), self.span_w(4),
                                         self.body_bottom() - top() - theme.S(44)), stripe=False)
        self._right_panel = panel
        strip = theme.S(8)
        self._strip_item = self.create_image(0, 0, anchor="nw")
        self._strip_img = None

        pad = theme.S(12)
        field_h = theme.S(38)
        self._field_h = field_h
        self._field_rect = lambda: (panel()[0] + pad, panel()[1] + strip + theme.S(8), panel()[2] - 2 * pad, field_h)
        self._note_rect = lambda: (panel()[0] + pad, self._field_rect()[1] + field_h + theme.S(8),
                                   panel()[2] - 2 * pad, theme.S(22))
        self._list_rect = lambda: (panel()[0] + pad, self._note_rect()[1] + theme.S(22) + theme.S(8),
                                   panel()[2] - 2 * pad,
                                   panel()[3] + panel()[1] - (self._note_rect()[1] + theme.S(22) + theme.S(8)) - pad)

        self._field_items = {}
        self.hook(self._draw_right_top)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self, textvariable=self.search_var, bg=theme.PANEL_2, fg=theme.TEXT,
                                     insertbackground=theme.TEXT, relief="flat", bd=0, highlightthickness=0,
                                     font=theme.fpx(theme.SANS, 17))
        self.search_entry.bind("<KeyRelease>", lambda e: self._restyle_roster())
        self._hint = text.t("Drafting Search Hint")
        self._placeholder_on = False
        self._set_placeholder()
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", lambda e: self._set_placeholder())
        entry_h = line_height(theme.fpx(theme.SANS, 17)) + theme.S(2)
        self.put(self.search_entry, lambda: self._entry_rect(entry_h))

        self.right = kit.ScrollCanvas(self, theme.PANEL, on_size=self._on_right_size)
        self.put(self.right, self._list_rect, on_rect=self.right.fit)
        kit.on_click(self.right.canvas, self._on_right_click)
        cv = self.right.canvas
        cv.tag_bind("rowhot", "<Enter>", lambda e: cv.configure(cursor="hand2" if self.active is not None else ""))
        cv.tag_bind("rowhot", "<Leave>", lambda e: cv.configure(cursor=""))

    def _build_footer(self):
        """The bottom row: a status note after Home, then Reset, Save and Lock Seed (all the same size) on the right."""
        width = theme.BUTTON_W
        px = theme.S(width)
        gap = self.gutter()
        footer_y = lambda: self.footer_top()
        lock = GlassButton(self, text.t("Drafting Lock Button"), self._on_lock, kind="primary", width=width)
        save = GlassButton(self, text.t("Button Save"), self._on_save, kind="secondary", width=width)
        reset = GlassButton(self, text.t("Button Reset"), self._on_reset, kind="danger", width=width)
        h = theme.S(theme.FOOTER_H)
        self.put(lock, lambda: (self.right_edge() - px, footer_y(), px, h))
        self.put(save, lambda: (self.right_edge() - 2 * px - gap, footer_y(), px, h))
        self.put(reset, lambda: (self.right_edge() - 3 * px - 2 * gap, footer_y(), px, h))
        self._warn_item = self.text_note(
            "", lambda: (self.footer_left(), footer_y() + h // 2,
                         self.right_edge() - 3 * px - 3 * gap - self.footer_left()), color=theme.ACCENT_TEXT)

    def _set_warning(self, message):
        """Shows (or clears) the status message at the bottom."""
        self.set_note(self._warn_item, message)

    # ---------- the top of the right panel: colored strip, search box, note ----------

    def _entry_rect(self, entry_h):
        """Where the search box (the one real text field on this screen) sits inside the field."""
        fx, fy, fw, fh = self._field_rect()
        left = fx + 1 + theme.S(12) + theme.S(16) + theme.S(8)
        right = fx + fw - 1 - self._clear_room() - self._chip_room() - theme.S(8)
        return (left, fy + (fh - entry_h) / 2, max(10, right - left), entry_h)

    def _clear_room(self):
        """How much room the little clear-search cross takes at the right end of the field."""
        return theme.S(8) + theme.S(12) + theme.S(12)

    def _chip_room(self):
        """How much room the 'n undrafted' tag takes inside the field."""
        return kit.chip_width(text.t("Drafting Undrafted", n=self._undrafted), theme.fpx(theme.SANS, 15)) + theme.S(8)

    def _draw_right_top(self):
        """Draws (or moves) the colored strip, the search field and the 'n undrafted' tag - everything above the player list."""
        rx, ry, rw, rh = self._right_panel()
        strip = theme.S(8)
        band = theme.mix(theme.PANEL, theme.ACCENT, 0.55)
        img = gfx.gradient_bar(max(2, int(rw)), strip, band, band, False)
        if img is not None:
            self._strip_img = img
            self.itemconfigure(self._strip_item, image=img)
        self.coords(self._strip_item, int(rx), int(ry))

        self.delete("rtop")
        fx, fy, fw, fh = (int(v) for v in self._field_rect())
        kit.box(self, fx, fy, fx + fw, fy + fh, theme.PANEL_2, theme.LINE, ("rtop",))
        icon = gfx.icon_alpha("search", theme.S(16), theme.DIM)
        self._search_icon = icon
        if icon is not None:
            self.create_image(fx + 1 + theme.S(12), fy + fh / 2, image=icon, anchor="w", tags=("rtop",))
        chip_font = theme.fpx(theme.SANS, 15)
        label = text.t("Drafting Undrafted", n=self._undrafted)
        chip_x = fx + fw - 1 - self._clear_room() - kit.chip_width(label, chip_font)
        kit.draw_chip(self, chip_x, fy + theme.S(5), label, chip_font,
                      theme.mix(theme.BTN_TOP, theme.BTN_BOTTOM, 0.5), theme.BTN_EDGE, theme.TEXT,
                      tags=("rtop",), height=fh - theme.S(10))
        cross = gfx.icon_alpha("x", theme.S(14), theme.DIM)
        self._cross_icon = cross
        if cross is not None:
            self.create_image(fx + fw - 1 - theme.S(12), fy + fh / 2, image=cross, anchor="e",
                              tags=("rtop", "clear"))
        if not self._field_items.get("bound"):
            self._field_items["bound"] = True
            self.tag_bind("clear", "<Button-1>", lambda e: self._clear_search())
            self.tag_bind("clear", "<Enter>", lambda e: self.configure(cursor="hand2"))
            self.tag_bind("clear", "<Leave>", lambda e: self.configure(cursor=""))
        self._draw_note()

    def _draw_note(self):
        """Writes the line above the list: which team and slot you're drafting for, or a hint to pick a slot."""
        self.delete("rnote")
        nx, ny, nw, nh = (int(v) for v in self._note_rect())
        mid = ny + nh / 2
        font = theme.FONT_NOTE
        if self.active is None:
            self.create_text(nx, mid, text=fit_text(text.t("Drafting Select Hint"), font, nw), anchor="w",
                             fill=theme.DIM, font=font, tags=("rnote",))
        else:
            ti, si = self.active
            team = self.app.teams[ti]
            chosen = team.slot_min_rank[si]
            tier = None if chosen == "Any" else chosen
            req = text.t("Drafting Any Rank") if tier is None else text.t("Drafting Tier Only", tier=tier)
            template = text.t("Drafting Note", team="\u0001", slot=si + 1, req=req)
            before, _sep, after = template.partition("\u0001")
            if self._shown_count == 0:
                after = after + " " + text.t("Drafting No Match")
            side = theme.S(8)
            x = nx
            self.create_rectangle(x, mid - side / 2, x + side, mid + side / 2, fill=theme.ACCENT, outline="",
                                  tags=("rnote",))
            x += side + theme.S(8)
            for piece, color in ((before, theme.DIM), (team.name, theme.ACCENT_TEXT), (after, theme.DIM)):
                if not piece:
                    continue
                room = nx + nw - x
                shown = fit_text(piece, font, room)
                self.create_text(x, mid, text=shown, anchor="w", fill=color, font=font, tags=("rnote",))
                x += text_width(font, shown)
                if shown != piece:
                    break

    # ---------- search box placeholder ----------

    def _set_placeholder(self):
        """Shows the faint 'Search by player name' hint while the box is empty and unfocused."""
        if not self.search_var.get():
            self._placeholder_on = True
            self.search_entry.configure(fg=theme.DIM)
            self.search_var.set(self._hint)

    def _clear_placeholder(self, _event=None):
        """Removes the hint when the box gets focus."""
        if self._placeholder_on:
            self._placeholder_on = False
            self.search_var.set("")
            self.search_entry.configure(fg=theme.TEXT)

    def _query(self):
        """What's typed in the search box (nothing if it's only showing the hint)."""
        return "" if self._placeholder_on else self.search_var.get().strip().lower()

    # ---------- measuring ----------

    def _row_heights(self):
        """Works out how tall the captain row and the slot rows must be so both name lines always fit inside the box."""
        block = line_height(self._fonts["name"]) + line_height(self._fonts["sub"])
        return max(theme.S(CAP_H), block + theme.S(10)), max(theme.S(SLOT_H), block + theme.S(10))

    def _card_height(self, team):
        """How tall one team card is."""
        cap_h, slot_h = self._row_heights()
        gap = theme.S(ROW_GAP)
        rows = cap_h + gap + len(team.slots) * (slot_h + gap)
        return 2 + theme.S(HEADER_H) + 2 * theme.S(CARD_PAD) + rows - gap

    # ---------- teams (left canvas) ----------

    def _on_left_size(self, width):
        """Draws the team cards again when the canvas gets a new width."""
        self._commit_names()
        self._draw_teams(width)

    def _draw_teams(self, width):
        """Draws every team card (header, captain row and draft slots) on the left canvas."""
        cv = self.left.canvas
        cv.delete("all")
        self._slot_refs = {}
        self._head_refs = {}
        self._card_y = {}
        gap = theme.S(theme.GUTTER)
        card_w = max(40, (width - gap) // 2)
        y = 0
        teams = self.app.teams
        for start in range(0, len(teams), 2):
            pair = list(range(start, min(start + 2, len(teams))))
            row_h = max(self._card_height(teams[ti]) for ti in pair)
            for ti in pair:
                x = (ti - start) * (card_w + gap)
                self._draw_card(cv, ti, x, y, card_w, self._card_height(teams[ti]))
                self._card_y[ti] = (y, y + self._card_height(teams[ti]))
            y += row_h + gap
        self.left.set_content_height(max(0, y - gap))
        for (ti, si) in list(self._slot_refs):
            self._style_slot(ti, si)

    def _draw_card(self, cv, ti, x, y, w, h):
        """Draws one team's card: border, colored header with the team name and a pencil, the captain row and the slots."""
        team = self.app.teams[ti]
        h1, h2 = theme.team_hue(ti)
        card_bg = theme.team_body_color((h1, h2))
        border = theme.mix(theme.BASE, h1, 0.60)
        kit.box(cv, x, y, x + w, y + h, card_bg, border)
        hx, hy, hw, hh = x + 1, y + 1, w - 2, theme.S(HEADER_H)
        head_tag = f"head:{ti}"
        kit.draw_gradient(cv, hx, hy, hw, hh, h1, h2, True, ("hot", head_tag))
        name_font = theme.fpx(theme.SANS, 20)
        pencil = gfx.icon_alpha("pencil", theme.S(16), theme.HEADER_INK)
        side = theme.S(16)
        room = hw - 2 * theme.S(16) - side - theme.S(8)
        title = cv.create_text(hx + theme.S(16), hy + hh / 2, text=fit_text(team.name, name_font, room), anchor="w",
                               fill=theme.HEADER_INK, font=name_font, tags=("hot", head_tag))
        if pencil is not None:
            cv.create_image(hx + hw - theme.S(16) - side, hy + hh / 2, image=pencil, anchor="w", tags=("hot", head_tag))
        self._head_refs[ti] = {"title": title, "x": hx, "y": hy, "w": hw, "h": hh, "font": name_font, "room": room}

        cap_h, slot_h = self._row_heights()
        gap = theme.S(ROW_GAP)
        pad = theme.S(CARD_PAD)
        rx = x + 1 + pad
        rw = w - 2 - 2 * pad
        ry = hy + hh + pad
        self._draw_captain_row(cv, team, rx, ry, rw, cap_h, card_bg)
        ry += cap_h + gap
        for si in range(len(team.slots)):
            self._draw_slot_frame(cv, ti, si, rx, ry, rw, slot_h, card_bg, h1)
            self._draw_slot_content(ti, si)
            ry += slot_h + gap

    def _draw_icons_right(self, cv, player, right, y_mid, bg, tags):
        """Draws the player's platform icon and preferred-role badges stacked against `right`. Gives back the x where they start."""
        side = kit.badge_side(14)
        gap = theme.S(4)
        roles = [r for r in player.preferred_roles if r]
        roles_w = len(roles) * side + max(0, len(roles) - 1) * gap
        x = right - roles_w
        for role in roles:
            kit.draw_role_badge(cv, x, y_mid - side / 2, role, 14, bg, tags)
            x += side + gap
        left = right - roles_w
        plat_w = kit.platform_width(player.platform, 18)
        if plat_w:
            left -= theme.S(8) + plat_w
            kit.draw_platform(cv, left, y_mid - theme.S(18) / 2, player.platform, 18, tags)
        return left

    def _draw_names(self, cv, player, x, y, h, room, tags, name_color):
        """Draws the two stacked name lines (Twitch/YouTube name, then in-game name) centered in a row of height h."""
        name_h = line_height(self._fonts["name"])
        block = name_h + line_height(self._fonts["sub"])
        top = y + (h - block) / 2
        cv.create_text(x, top, text=fit_text(player.twitch, self._fonts["name"], room), anchor="nw",
                       fill=name_color, font=self._fonts["name"], tags=tags)
        cv.create_text(x, top + name_h, text=fit_text(player.ign, self._fonts["sub"], room), anchor="nw",
                       fill=theme.DIM, font=self._fonts["sub"], tags=tags)

    def _draw_captain_row(self, cv, team, x, y, w, h, card_bg):
        """The captain's row at the top of a card: C box, names, platform, roles and peak rank."""
        row_bg, _edge = theme.row_colors(card_bg)
        bg = theme.mix(row_bg, theme.ACCENT, 0.30)
        edge = theme.mix(card_bg, theme.ACCENT, 0.65)
        kit.box(cv, x, y, x + w, y + h, bg, edge)
        side = theme.S(NUM_SIDE)
        bx, by = x + 1 + theme.S(8), y + (h - side) / 2
        kit.box(cv, bx, by, bx + side, by + side, theme.ACCENT, theme.ACCENT_EDGE)
        cv.create_text(bx + side / 2, by + side / 2, text="C", fill=theme.ACCENT_INK, font=theme.FONT_STEP)
        player = team.captain
        right = x + w - 1 - theme.S(8)
        tag_w = kit.draw_rank_tag(cv, right - kit.rank_tag_width(player.peak_rank, theme.fpx(theme.SANS, 15)),
                                  y + h / 2, player.peak_rank, theme.fpx(theme.SANS, 15))
        left = self._draw_icons_right(cv, player, right - tag_w - theme.S(12), y + h / 2, bg, ())
        name_x = bx + side + theme.S(8)
        self._draw_names(cv, player, name_x, y, h, left - theme.S(8) - name_x, (), theme.TEXT)

    def _draw_slot_frame(self, cv, ti, si, x, y, w, h, card_bg, hue):
        """Draws the parts of a slot row that never change shape: the border, the fill and the number box. Registers the slot."""
        slot_tag = f"slot:{ti}:{si}"
        outer, inner = kit.box(cv, x, y, x + w, y + h, card_bg, theme.LINE, ("hot", slot_tag))
        side = theme.S(NUM_SIDE)
        bx, by = x + 1 + theme.S(8), y + (h - side) / 2
        nouter, ninner = kit.box(cv, bx, by, bx + side, by + side, theme.PANEL_2, theme.LINE, ("hot", slot_tag))
        number = cv.create_text(bx + side / 2, by + side / 2, text=str(si + 1), fill=theme.FAINT, font=theme.FONT_STEP,
                                tags=("hot", slot_tag))
        drop_w, drop_h = theme.S(DROP_W), theme.S(DROP_H)
        dx = x + w - 1 - theme.S(8) - drop_w
        dy = y + (h - drop_h) / 2
        drop_tag = f"drop:{ti}:{si}"
        douter, dinner = kit.box(cv, dx, dy, dx + drop_w, dy + drop_h, theme.PANEL_2, theme.LINE, ("hot", drop_tag))
        arrow_side = theme.S(14)
        arrow = cv.create_image(dx + drop_w - theme.S(8), dy + drop_h / 2, anchor="e", tags=("hot", drop_tag))
        dtext = cv.create_text(dx + theme.S(10), dy + drop_h / 2, anchor="w", font=self._fonts["small"],
                               tags=("hot", drop_tag))
        self._slot_refs[(ti, si)] = {
            "x": x, "y": y, "w": w, "h": h, "outer": outer, "inner": inner, "nouter": nouter, "ninner": ninner,
            "number": number, "douter": douter, "dinner": dinner, "dtext": dtext, "arrow": arrow,
            "arrow_side": arrow_side, "drop": (dx, dy, drop_w, drop_h), "card_bg": card_bg, "hue": hue,
            "name_x": bx + side + theme.S(8),
        }

    def _style_slot(self, ti, si):
        """Recolors one slot row (active, filled or empty) and its rank picker. Nothing is redrawn from scratch."""
        ref = self._slot_refs.get((ti, si))
        if ref is None:
            return
        cv = self.left.canvas
        team = self.app.teams[ti]
        player = team.slots[si]
        row_fill, row_edge = theme.row_colors(ref["card_bg"])
        active = self.active == (ti, si)
        if active:
            bg, edge = theme.mix(row_fill, theme.ACCENT, 0.28), theme.ACCENT_TEXT
        elif player:
            bg, edge = row_fill, row_edge
        else:
            bg, edge = ref["card_bg"], theme.mix(ref["card_bg"], ref["hue"], 0.75)
        cv.itemconfigure(ref["outer"], fill=edge)
        cv.itemconfigure(ref["inner"], fill=bg)
        cv.itemconfigure(ref["nouter"], fill=edge)
        cv.itemconfigure(ref["ninner"], fill=theme.ACCENT_TEXT if active and not player else theme.PANEL_2)
        cv.itemconfigure(ref["number"], fill=theme.ACCENT_INK if active else theme.FAINT)
        locked = player is not None
        cv.itemconfigure(ref["dinner"], fill=theme.PANEL if locked else theme.PANEL_2)
        room = ref["drop"][2] - theme.S(10) - theme.S(8) - ref["arrow_side"] - theme.S(4)
        cv.itemconfigure(ref["dtext"], text=fit_text(team.slot_min_rank[si], self._fonts["small"], room),
                         fill=theme.DIM if locked else theme.TEXT)
        arrow = gfx.icon_alpha("down", ref["arrow_side"], theme.DIM if locked else theme.TEXT)
        ref["arrow_img"] = arrow
        if arrow is not None:
            cv.itemconfigure(ref["arrow"], image=arrow)

    def _draw_slot_content(self, ti, si):
        """Draws what's inside a slot row right now: the player's names and icons, or the 'Empty slot' line."""
        ref = self._slot_refs.get((ti, si))
        if ref is None:
            return
        cv = self.left.canvas
        cv.delete(f"cont:{ti}:{si}")
        tags = ("hot", f"slot:{ti}:{si}", f"cont:{ti}:{si}")
        team = self.app.teams[ti]
        player = team.slots[si]
        row_fill, _edge = theme.row_colors(ref["card_bg"])
        if not player:
            font = self._fonts["name"]
            cv.create_text(ref["name_x"], ref["y"] + ref["h"] / 2, text=text.t("Drafting Empty Slot"), anchor="w",
                           fill=theme.DIM, font=font, tags=tags)
            return
        dx = ref["drop"][0]
        right = dx - theme.S(8)
        left = self._draw_icons_right(cv, player, right, ref["y"] + ref["h"] / 2, row_fill, tags)
        self._draw_names(cv, player, ref["name_x"], ref["y"], ref["h"], left - theme.S(8) - ref["name_x"], tags,
                         theme.TEXT)

    def _update_slot(self, ti, si):
        """Refreshes just one slot row (its look, its content and its rank picker)."""
        team = self.app.teams[ti]
        player = team.slots[si]
        if player:
            # Drafted: lock the selector to the player's tier until undrafted.
            team.slot_min_rank[si] = strip_subdivision(player.peak_rank)
        self._style_slot(ti, si)
        self._draw_slot_content(ti, si)

    def _on_left_click(self, tags, event):
        """Works out what on the team cards was clicked: a header (rename), a rank picker, or a slot."""
        for tag in tags:
            kind, _sep, rest = tag.partition(":")
            if kind == "head":
                self._begin_rename(int(rest))
                return
            if kind == "drop":
                ti, si = (int(v) for v in rest.split(":"))
                self._open_rank_menu(ti, si)
                return
            if kind == "slot":
                ti, si = (int(v) for v in rest.split(":"))
                self._on_slot_click(ti, si)
                return

    # ---------- renaming a team ----------

    def _begin_rename(self, ti):
        """Swaps the team's name for a text box over its header so it can be changed."""
        self._commit_names()
        ref = self._head_refs.get(ti)
        if ref is None:
            return
        cv = self.left.canvas
        entry = tk.Entry(cv, relief="flat", bd=0, highlightthickness=1, highlightbackground=theme.HEADER_INK,
                         highlightcolor=theme.HEADER_INK, font=ref["font"], fg=theme.HEADER_INK, insertbackground=theme.HEADER_INK,
                         bg=theme.mix(theme.mix(*theme.team_hue(ti), 0.3), theme.PANEL_2, 0.45))
        entry.insert(0, self.app.teams[ti].name)
        pad = theme.S(16)
        item = cv.create_window(ref["x"] + pad, ref["y"] + ref["h"] / 2, anchor="w", window=entry,
                                width=max(theme.S(120), ref["w"] - 2 * pad - theme.S(32)),
                                height=ref["h"] - theme.S(10))
        entry.select_range(0, "end")
        entry.focus_set()
        entry.bind("<Return>", lambda e: self._commit_names())
        entry.bind("<Escape>", lambda e: self._cancel_rename())
        entry.bind("<FocusOut>", lambda e: self._commit_names())
        self._rename = {"ti": ti, "entry": entry, "item": item}

    def _cancel_rename(self):
        """Throws away what was typed in the rename box."""
        pending, self._rename = self._rename, None
        if pending is not None:
            self.left.canvas.delete(pending["item"])
            pending["entry"].destroy()

    def _commit_names(self):
        """Keeps what was typed in a rename box (blank names are ignored) and goes back to showing the name.
        Called before Save, Lock Seed and any redraw so a rename in progress is never lost."""
        pending, self._rename = self._rename, None
        if pending is None:
            return
        new_name = pending["entry"].get().strip()
        self.left.canvas.delete(pending["item"])
        pending["entry"].destroy()
        ti = pending["ti"]
        if new_name:
            self.app.teams[ti].name = new_name
            ref = self._head_refs.get(ti)
            if ref is not None:
                self.left.canvas.itemconfigure(ref["title"], text=fit_text(new_name, ref["font"], ref["room"]))
            if self.active is not None:
                self._draw_note()

    # ---------- rank picker ----------

    def _open_rank_menu(self, ti, si):
        """Opens the pick list under a slot's rank box (nothing happens once the slot has a player in it)."""
        team = self.app.teams[ti]
        ref = self._slot_refs.get((ti, si))
        if ref is None or team.slots[si] is not None:
            return
        cv = self.left.canvas
        dx, dy, dw, dh = ref["drop"]
        x_root = cv.winfo_rootx() + dx - cv.canvasx(0)
        top_root = cv.winfo_rooty() + dy - cv.canvasy(0)
        self._menu.open(cv, x_root, top_root, top_root + dh, dw, TIER_OPTIONS, team.slot_min_rank[si],
                        lambda value, t=ti, s=si: self._set_min_rank(t, s, value))

    def _set_min_rank(self, ti, si, value):
        """Runs when you change a slot's rank picker: remembers it and filters the roster to match."""
        self.app.teams[ti].slot_min_rank[si] = value
        self._style_slot(ti, si)
        self._set_active((ti, si))
        self._restyle_roster()

    # ---------- interaction handlers ----------

    def _set_active(self, new_active):
        """Marks a slot as the one we're drafting for and restyles the old and new slot rows."""
        old_active = self.active
        self.active = new_active
        if old_active is not None and old_active != new_active:
            self._style_slot(*old_active)
        if new_active is not None:
            self._style_slot(*new_active)

    def _on_slot_click(self, ti, si):
        """Clicking a filled slot sends the player back to the pool; clicking an empty one selects it (or deselects it)."""
        self._commit_names()
        team = self.app.teams[ti]
        if team.slots[si] is not None:
            # Click on a drafted slot: undraft, return the player to the pool, and unlock the rank picker.
            team.clear_slot(si)
            self._set_active(None)
            self._update_slot(ti, si)
            self._restyle_roster()  # pool membership changed
            return

        if self.active == (ti, si):
            self._set_active(None)  # click the active empty slot again to deselect
        else:
            self._set_active((ti, si))
        self._restyle_roster()  # filtering changed, pool membership did not

    def _assign_player(self, player):
        """Puts the clicked player in the active slot, then jumps to the next open slot."""
        ti, si = self.active
        team = self.app.teams[ti]
        team.assign(si, player)          # _update_slot below locks the selector to their tier
        self._update_slot(ti, si)

        target = next_open_slot(self.app.teams, ti, si)
        self._set_active(target)
        if target is not None:
            ref = self._slot_refs.get(target)
            if ref is not None:
                self.left.ensure_visible(ref["y"], ref["y"] + ref["h"])

        self._restyle_roster()  # pool membership changed

    # ---------- roster (right canvas) ----------

    def _on_right_size(self, width):
        """Draws the player rows again when the canvas gets a new width."""
        self._draw_roster(width)
        self._restyle_roster(force=True)

    def _roster_row_h(self):
        """How tall one roster row is."""
        block = line_height(self._fonts["name"]) + theme.S(2) + line_height(self._fonts["small"])
        return max(theme.S(ROSTER_H), block + theme.S(14))

    def _draw_roster(self, width):
        """Draws one row for every player who could be drafted, once; rows are shown, hidden and moved afterwards."""
        cv = self.right.canvas
        cv.delete("all")
        everyone = [p for p in self.app.players if not p.captain]
        everyone.sort(key=lambda p: rank_sort_key(p.peak_rank))
        self._roster_order = [p.ign for p in everyone]
        self._roster_refs = []
        self._selectable_drawn = None
        row_w = width - theme.S(4)
        row_h = self._roster_row_h()
        name_h = line_height(self._fonts["name"])
        block = name_h + theme.S(2) + line_height(self._fonts["small"])
        for index, p in enumerate(everyone):
            role = p.preferred_roles[0] if p.preferred_roles else None
            color = theme.ROLE_COLOR.get(role, theme.DIM)
            left_bg = theme.mix(theme.BASE, color, 0.34 if theme.MODE == "dark" else 0.22)
            edge = theme.mix(theme.BASE, color, 0.55)
            tags = ("rowhot", f"rr:{index}")
            kit.box(cv, 0, 0, row_w, row_h, left_bg, edge, tags)
            cv.addtag_withtag(f"rre:{index}", cv.find_withtag(f"rr:{index}")[0])
            side = kit.badge_side(14)
            gap = theme.S(4)
            roles = [r for r in p.preferred_roles if r]
            roles_w = len(roles) * side + max(0, len(roles) - 1) * gap
            rx = row_w - theme.S(12) - roles_w
            for r in roles:
                kit.draw_role_badge(cv, rx, (row_h - side) / 2, r, 14, left_bg, tags)
                rx += side + gap
            top = (row_h - block) / 2
            x = theme.S(12)
            room = row_w - roles_w - theme.S(12) - x - theme.S(12)
            line1 = kit.draw_text(cv, x, top, p.twitch, self._fonts["name"], theme.TEXT, room, "nw", tags)
            shown_w = text_width(self._fonts["name"], fit_text(p.twitch, self._fonts["name"], room))
            plat_w = kit.platform_width(p.platform, 18)
            if plat_w and shown_w + theme.S(8) + plat_w <= room:
                kit.draw_platform(cv, x + shown_w + theme.S(8), top + (name_h - theme.S(18)) / 2, p.platform, 18, tags)
            y2 = top + name_h + theme.S(2)
            ign_room = room
            ign = fit_text(p.ign, self._fonts["small"], ign_room)
            cv.create_text(x, y2, text=ign, anchor="nw", fill=theme.DIM, font=self._fonts["small"], tags=tags)
            ign_w = text_width(self._fonts["small"], ign)
            tag_x = x + ign_w + theme.S(12)
            if tag_x + kit.rank_tag_width(p.peak_rank, theme.fpx(theme.SANS, 15)) <= x + room:
                kit.draw_rank_tag(cv, tag_x, y2 + line_height(self._fonts["small"]) / 2, p.peak_rank,
                                  theme.fpx(theme.SANS, 15), tags)
            del line1
            self._roster_refs.append({"player": p, "edge": edge, "shown": True, "y": 0, "tag": f"rr:{index}"})

    def _on_right_click(self, tags, event):
        """Drafts the clicked player into the selected slot (nothing happens if no slot is selected)."""
        for tag in tags:
            if tag.startswith("rr:"):
                if self.active is not None:
                    self._assign_player(self._roster_refs[int(tag[3:])]["player"])
                return

    @staticmethod
    def _fuzzy_match(query, name):
        """True if the typed letters show up in the name in order, even with gaps ("pxl" matches "Pixel")."""
        name_l = name.lower()
        if query in name_l:
            return True
        it = iter(name_l)
        return all(ch in it for ch in query)

    def _clear_search(self):
        """Empties the search box and shows the full roster again."""
        self._placeholder_on = False
        self.search_var.set("")
        self.search_entry.configure(fg=theme.TEXT)
        self._set_placeholder()
        self._restyle_roster()

    def _restyle_roster(self, force=False):
        """Shows only the undrafted players who match the rank filter and search, packs them together at the top,
        and updates the note and the count. Rows are only hidden, shown or moved - never rebuilt."""
        if not self._roster_refs and not force:
            return
        assigned = {p.ign for t in self.app.teams for p in t.slots if p is not None}
        tier = None
        query = self._query()
        if self.active is not None:
            ti, si = self.active
            chosen = self.app.teams[ti].slot_min_rank[si]
            tier = None if chosen == "Any" else chosen
        cv = self.right.canvas
        selectable = self.active is not None
        row_h = self._roster_row_h()
        gap = theme.S(ROSTER_GAP)
        y = 0
        shown = 0
        for index, ref in enumerate(self._roster_refs):
            p = ref["player"]
            rank_ok = self.active is None or tier is None or matches_tier(p.peak_rank, tier)
            search_ok = not query or self._fuzzy_match(query, p.ign) or self._fuzzy_match(query, p.twitch)
            visible = p.ign not in assigned and rank_ok and search_ok
            if visible:
                shown += 1
                if ref["y"] != y:
                    cv.move(ref["tag"], 0, y - ref["y"])
                    ref["y"] = y
                if not ref["shown"]:
                    cv.itemconfigure(ref["tag"], state="normal")
                    ref["shown"] = True
                y += row_h + gap
            elif ref["shown"]:
                cv.itemconfigure(ref["tag"], state="hidden")
                ref["shown"] = False
        if self._selectable_drawn != selectable:
            self._selectable_drawn = selectable
            for index, ref in enumerate(self._roster_refs):
                cv.itemconfigure(f"rre:{index}", fill=theme.ACCENT_TEXT if selectable else ref["edge"])
        self.right.set_content_height(max(0, y - gap))
        undrafted = len(self._roster_order) - len([i for i in self._roster_order if i in assigned])
        changed = undrafted != self._undrafted or shown != self._shown_count
        self._undrafted, self._shown_count = undrafted, shown
        if changed:
            self.relayout()
        self._draw_note()

    # ---------- footer actions ----------

    def _on_lock(self):
        """Moves on to the next screen. If some slots are empty, it warns first and needs a second click."""
        self._commit_names()
        incomplete = [t for t in self.app.teams if not t.is_full()]
        if incomplete and not self._lock_confirmed:
            names = ", ".join(t.name for t in incomplete)
            self._set_warning(text.t("Drafting Not Full", teams=names))
            self._lock_confirmed = True
            return
        self._lock_confirmed = False
        self.app.show_screen("tournament_type")

    def _on_reset(self):
        """After a warning, empties every slot and puts everybody back in the pool."""
        if not dialogs.confirm_reset(self.app):
            return
        self._commit_names()
        for ti, team in enumerate(self.app.teams):
            team.slots = [None] * len(team.slots)
            team.slot_min_rank = ["Any"] * len(team.slot_min_rank)
        self.active = None
        for (ti, si) in list(self._slot_refs):
            self._update_slot(ti, si)
        self._lock_confirmed = False
        self._set_warning("")
        self._restyle_roster()

    def _on_save(self):
        """Saves the current draft to the save file and tells you it worked."""
        self._commit_names()
        save_state(serialize_app_state(self.app), status="Seed")
        dialogs.notify_saved(self.app)

    # ---------- keeping state across a light/dark switch ----------

    def capture_state(self):
        """Remembers the selected slot, the search words, the pending warning and where both lists are scrolled to."""
        self._commit_names()
        return {"active": self.active, "query": "" if self._placeholder_on else self.search_var.get(),
                "lock": self._lock_confirmed, "left": self.left.canvas.yview()[0],
                "right": self.right.canvas.yview()[0]}

    def restore_state(self, state):
        """Puts the selected slot, search words, warning and scroll positions back after the screen was rebuilt."""
        self._lock_confirmed = state.get("lock", False)
        if state.get("query"):
            self._placeholder_on = False
            self.search_var.set(state["query"])
            self.search_entry.configure(fg=theme.TEXT)
        if state.get("active") is not None:
            self._set_active(state["active"])
        self._restyle_roster(force=True)
        self.left.canvas.yview_moveto(state.get("left", 0))
        self.right.canvas.yview_moveto(state.get("right", 0))

    def destroy(self):
        """Closes the rank pick list if it's open before the screen goes away."""
        self._menu.close()
        super().destroy()
