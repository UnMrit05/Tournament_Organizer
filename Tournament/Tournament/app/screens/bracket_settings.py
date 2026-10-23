"""The bracket settings screen: set the seed order by dragging, pick the bracket type, then build the bracket.
The seed rows and the three format cards are drawn straight onto canvases, so the screen opens in one go."""

from app.data import bracket as B
from app.data.save_manager import save_state, serialize_app_state
from app.ui import dialogs, gfx, kit, text, theme
from app.ui.stage import Stage
from app.ui.widgets import GlassButton, fit_text, line_height


FORMATS = [
    ("single", "Single Elimination Name", 3),
    ("double", "Double Elimination Name", 1),
    ("league", "League Name", 2),
]

ROW_H = 52
NUMBER_W = 56
DIAGRAM_W = 200
DIAGRAM_BOX = (152, 72)    # reference pixels the little bracket drawing is scaled to

# The little pictures: lines are lists of points and boxes are (x, y, w, h), all drawn in a 132 x 64 space.
DIAGRAMS = {
    "single": {
        "lines": [[(28, 7), (40, 7), (40, 15), (52, 15)], [(28, 23), (40, 23), (40, 15)],
                  [(28, 39), (40, 39), (40, 47), (52, 47)], [(28, 55), (40, 55), (40, 47)],
                  [(80, 15), (92, 15), (92, 31), (104, 31)], [(80, 47), (92, 47), (92, 31)]],
        "boxes": [(0, 2, 28, 10), (0, 18, 28, 10), (0, 34, 28, 10), (0, 50, 28, 10),
                  (52, 10, 28, 10), (52, 42, 28, 10), (104, 26, 28, 10)],
    },
    "double": {
        "lines": [[(28, 6), (40, 6), (40, 12), (52, 12)], [(28, 18), (40, 18), (40, 12)],
                  [(28, 44), (40, 44), (40, 50), (52, 50)], [(28, 56), (40, 56), (40, 50)],
                  [(80, 12), (92, 12), (92, 32), (104, 32)], [(80, 50), (92, 50), (92, 32)]],
        "boxes": [(0, 2, 28, 8), (0, 14, 28, 8), (52, 8, 28, 8), (0, 40, 28, 8), (0, 52, 28, 8),
                  (52, 46, 28, 8), (104, 27, 28, 10)],
    },
    "league": {
        "lines": [[(58, 32), (68, 32)], [(102, 19), (110, 19), (110, 32), (118, 32)], [(102, 45), (110, 45), (110, 32)]],
        "boxes": [(c * 14, 8 + r * 14, 11, 11) for r in range(4) for c in range(4)]
                 + [(76, 14, 26, 10), (76, 40, 26, 10)],
    },
}


class BracketSettingsScreen(Stage):
    """Screen for ordering the teams and choosing single, double or league format."""

    STEP = 3
    WATERMARK = "center"

    def __init__(self, parent, app):
        """Sets up the screen: seed order list, format cards and the bottom buttons."""
        super().__init__(parent, app, "bracket_settings")
        self.set_title(text.t("Bracket Settings Heading"))

        # Keep the seed order on the app object (same list) so it survives
        # navigating away and back, and is what Save serializes.
        same_teams = (app.bracket_order is not None
                      and {id(t) for t in app.bracket_order} == {id(t) for t in app.teams}
                      and len(app.bracket_order) == len(app.teams))
        self.order = app.bracket_order if same_teams else list(app.teams)
        app.bracket_order = self.order
        self.selected_format = app.bracket_type or "single"
        app.bracket_type = self.selected_format

        self._drag_index = None
        self._row_teams = []          # which team each drawn row currently shows
        self._formats_drawn = None

        self._build_order_side()
        self._build_format_side()
        self._build_footer()

    # ---------- skeleton ----------

    def _build_order_side(self):
        """The left side: the seed order title and a panel holding the draggable rows on one scrolling canvas."""
        top = lambda: self.body_top()
        list_top = lambda: top() + theme.S(44)
        self.section(text.t("Seed Order Label"), lambda: (self.col_x(0), top(), self.span_w(5)))
        panel = self.draw_panel(lambda: (self.col_x(0), list_top(), self.span_w(5), self.body_bottom() - list_top()))
        pad = theme.S(12)
        self.seeds = kit.ScrollCanvas(self, theme.PANEL, on_size=self._draw_order)
        self.put(self.seeds, lambda: (panel()[0] + pad, panel()[1] + pad, panel()[2] - 2 * pad,
                                      panel()[3] - pad - theme.S(4)), on_rect=self.seeds.fit)
        cv = self.seeds.canvas
        cv.bind("<ButtonPress-1>", self._on_press)
        cv.bind("<B1-Motion>", self._drag_motion)
        cv.bind("<ButtonRelease-1>", self._drag_end)
        cv.tag_bind("grab", "<Enter>", lambda e: cv.configure(cursor="fleur"))
        cv.tag_bind("grab", "<Leave>", lambda e: cv.configure(cursor=""))
        cv.tag_bind("push", "<Enter>", lambda e: cv.configure(cursor="hand2"))
        cv.tag_bind("push", "<Leave>", lambda e: cv.configure(cursor=""))
        self._tips = kit.TagTip(cv)
        self._tips.add("tip_up", text.t("Tip Move Up"))
        self._tips.add("tip_down", text.t("Tip Move Down"))

    def _build_format_side(self):
        """The right side: the Bracket type title and three big format cards that share the height."""
        top = lambda: self.body_top()
        self.section(text.t("Bracket Type Label"), lambda: (self.col_x(5), top(), self.span_w(7)))
        self.hook(self._draw_formats)
        for key, _name_key, _hue in FORMATS:
            self.tag_bind(f"fmt:{key}", "<Button-1>", lambda e, k=key: self._pick_format(k))
            self.tag_bind(f"fmt:{key}", "<Enter>", lambda e: self.configure(cursor="hand2"))
            self.tag_bind(f"fmt:{key}", "<Leave>", lambda e: self.configure(cursor=""))

    def _format_rect(self, index, count):
        """Where format card `index` goes: the cards split the space under the title evenly."""
        gap = self.gutter()
        top = self.body_top() + theme.S(44)
        total = self.body_bottom() - top
        height = (total - (count - 1) * gap) // count
        return (self.col_x(5), top + index * (height + gap), self.span_w(7), height)

    def _build_footer(self):
        """The bottom row: Back on the left, a note, then Save and Confirm on the right."""
        footer_y = lambda: self.footer_top()
        h = theme.S(theme.FOOTER_H)
        gap = self.gutter()
        back = GlassButton(self, text.t("Button Back"), self._on_back, kind="secondary")
        save = GlassButton(self, text.t("Button Save"), self._on_save, kind="secondary")
        self.confirm_btn = GlassButton(self, text.t("Button Confirm"), self._on_confirm, kind="primary")
        self.put(back, lambda: (self.footer_left(), footer_y(), back.pixel_width, h))
        self.put(self.confirm_btn, lambda: (self.right_edge() - self.confirm_btn.pixel_width, footer_y(),
                                            self.confirm_btn.pixel_width, h))
        self.put(save, lambda: (self.right_edge() - self.confirm_btn.pixel_width - gap - save.pixel_width,
                                footer_y(), save.pixel_width, h))
        left = lambda: self.footer_left() + back.pixel_width + gap
        right = lambda: self.right_edge() - self.confirm_btn.pixel_width - save.pixel_width - 2 * gap
        self._status_item = self.text_note("", lambda: (left(), footer_y() + h // 2, right() - left()),
                                           color=theme.ACCENT_TEXT)
        if len(self.order) < 2:
            self.confirm_btn.configure(state="disabled")
            self.set_note(self._status_item, text.t("Need Two Teams"))

    # ---------- format cards (drawn on the screen canvas) ----------

    def _hint_for(self, key):
        """The little explanation for a format (team count, byes, how it works)."""
        n = len(self.order)
        size = B.next_power_of_two(max(n, 2))
        values = {"teams": n, "size": size, "byes": size - n, "matches": n * (n - 1) // 2}
        names = {"single": "Single Elimination Hint", "double": "Double Elimination Hint", "league": "League Hint"}
        return text.t(names[key], **values)

    def _draw_formats(self):
        """Draws the three format cards. It only redraws when the size or the picked format changes."""
        if self._size[0] < 10:
            return
        signature = (self._size, self.selected_format, theme.MODE, theme.ACCENT)
        if signature == self._formats_drawn:
            return
        self._formats_drawn = signature
        self.delete("formats")
        count = len(FORMATS)
        for i, (key, name_key, hue) in enumerate(FORMATS):
            x, y, w, h = self._format_rect(i, count)
            self._draw_format_card(key, text.t(name_key), self._hint_for(key), hue, int(x), int(y), int(w), int(h))

    def _draw_format_card(self, key, name, hint, hue_index, x, y, w, h):
        """One format card: a colored picture area, the name and hint, and a tick box."""
        s = theme.S
        tags = ("formats", f"fmt:{key}")
        selected = key == self.selected_format
        h1, h2 = theme.team_hue(hue_index)
        card_bg = theme.team_body_color((h1, h2))
        border = 2 if selected else 1
        edge = theme.ACCENT_TEXT if selected else theme.mix(theme.BASE, h1, 0.60)
        self.create_rectangle(x, y, x + w, y + h, fill=edge, outline="", tags=tags)
        self.create_rectangle(x + border, y + border, x + w - border, y + h - border, fill=card_bg, outline="", tags=tags)

        art_x, art_y, art_w, art_h = x + border, y + border, s(DIAGRAM_W), h - 2 * border
        wash = gfx.vertical_swatch(art_w, art_h, [(0, theme.mix(theme.BASE, h1, 0.34)), (1, theme.mix(theme.BASE, h2, 0.10))])
        if wash is not None:
            self.create_image(art_x, art_y, image=wash, anchor="nw", tags=tags)
        else:
            self.create_rectangle(art_x, art_y, art_x + art_w, art_y + art_h, fill=theme.mix(theme.BASE, h1, 0.2),
                                  outline="", tags=tags)
        scale = s(DIAGRAM_BOX[0]) / 132
        ox = art_x + (art_w - 132 * scale) / 2
        oy = art_y + (art_h - 64 * scale) / 2
        color = theme.ACCENT_TEXT if selected else theme.DIM
        picture = DIAGRAMS[key]
        for pts in picture["lines"]:
            flat = [c for px, py in pts for c in (ox + px * scale, oy + py * scale)]
            self.create_line(*flat, fill=color, width=1, tags=tags)
        for bx, by, bw, bh in picture["boxes"]:
            self.create_rectangle(ox + bx * scale, oy + by * scale, ox + (bx + bw) * scale, oy + (by + bh) * scale,
                                  fill=theme.PANEL_2, outline=color, tags=tags)

        side = s(28)
        tx = x + w - border - s(24) - side
        ty = y + h / 2 - side / 2
        self.create_rectangle(tx, ty, tx + side, ty + side, fill=theme.ACCENT_EDGE if selected else theme.LINE,
                              outline="", tags=tags)
        inner = self.create_rectangle(tx + 1, ty + 1, tx + side - 1, ty + side - 1, fill=theme.PANEL_2, outline="",
                                      tags=tags)
        if selected:
            face = gfx.vertical_swatch(side - 2, side - 2, [(0, theme.ACCENT_HI), (1, theme.ACCENT_LO)])
            if face is not None:
                self.create_image(tx + 1, ty + 1, image=face, anchor="nw", tags=tags)
            else:
                self.itemconfigure(inner, fill=theme.ACCENT)
            iw = side - 2
            self.create_line(tx + 1 + iw * 0.24, ty + 1 + iw * 0.52, tx + 1 + iw * 0.43, ty + 1 + iw * 0.72,
                             tx + 1 + iw * 0.76, ty + 1 + iw * 0.28, fill=theme.ACCENT_INK, width=max(2, s(2)),
                             tags=tags)

        words_x = art_x + art_w + s(24)
        words_w = tx - s(24) - words_x
        title_font = theme.fpx(theme.SEMIBOLD, 18)
        hint_font = theme.fpx(theme.SANS, 19)
        title_h = line_height(title_font)
        title_item = self.create_text(words_x, 0, text=fit_text(name.upper(), title_font, words_w), anchor="nw",
                                      fill=theme.TEXT, font=title_font, tags=tags)
        hint_item = self.create_text(words_x, 0, text=hint, anchor="nw", fill=theme.DIM, font=hint_font,
                                     width=max(40, words_w), tags=tags)
        hint_h = self.bbox(hint_item)[3] - self.bbox(hint_item)[1]
        top = y + (h - (title_h + s(8) + hint_h)) / 2
        self.coords(title_item, words_x, top)
        self.coords(hint_item, words_x, top + title_h + s(8))

    def _pick_format(self, key):
        """Remembers which bracket type you clicked and updates the cards."""
        if key == self.selected_format:
            return
        self.selected_format = key
        self.app.bracket_type = key
        self._draw_formats()

    # ---------- seed order: drawn rows, pinned to positions ----------

    def _row_colors(self, team, dragging):
        """The colors of a seed row for this team: its own tint, or the accent while being dragged."""
        ti = self.app.teams.index(team) if team in self.app.teams else 0
        h1, h2 = theme.team_hue(ti)
        bg = theme.mix(theme.BASE, h1, 0.26 if theme.MODE == "dark" else 0.16)
        edge = theme.ACCENT_TEXT if dragging else theme.mix(theme.BASE, h1, 0.60)
        return h1, h2, bg, edge

    def _row_step(self):
        """How far apart (in pixels) the tops of two neighbouring rows are."""
        return theme.S(ROW_H) + theme.S(8)

    def _draw_order(self, width=None):
        """Draws every seed row from scratch (the first time, and when the list gets a new width)."""
        cv = self.seeds.canvas
        cv.delete("all")
        for i in range(len(self.order)):
            self._draw_order_row(i)
        self.seeds.set_content_height(max(0, len(self.order) * self._row_step() - theme.S(8)))

    def _draw_order_row(self, i):
        """Draws (or redraws) one row: the colored number, the drag dots, the team name and captain, and the up / down buttons."""
        s = theme.S
        cv = self.seeds.canvas
        width = self.seeds.width
        if width < 40:
            return
        team = self.order[i]
        row_tag = f"row:{i}"
        cv.delete(row_tag)
        dragging = self._drag_index == i
        h1, h2, bg, edge = self._row_colors(team, dragging)
        row_h = s(ROW_H)
        x0, y0 = 0, i * self._row_step()
        mid = y0 + row_h / 2
        grab = ("grab", row_tag)
        cv.create_rectangle(x0, y0, x0 + width, y0 + row_h, fill=edge, outline="", tags=grab)
        cv.create_rectangle(x0 + 1, y0 + 1, x0 + width - 1, y0 + row_h - 1, fill=bg, outline="", tags=grab)

        face = gfx.vertical_swatch(s(NUMBER_W), row_h - 2, [(0, h1), (1, h2)])
        if face is not None:
            cv.create_image(x0 + 1, y0 + 1, image=face, anchor="nw", tags=grab)
        else:
            cv.create_rectangle(x0 + 1, y0 + 1, x0 + 1 + s(NUMBER_W), y0 + row_h - 1, fill=h1, outline="", tags=grab)
        cv.create_text(x0 + 1 + s(NUMBER_W) / 2, mid, text=str(i + 1), fill=theme.HEADER_INK, font=theme.fpx(theme.SEMIBOLD, 20),
                       tags=grab)

        r = max(1, s(1.6))
        gx = x0 + 1 + s(NUMBER_W) + s(12)
        for cx in (s(4), s(10)):
            for cy in (s(4), s(10), s(16)):
                px, py = gx + cx, mid - s(10) + cy
                cv.create_oval(px - r, py - r, px + r, py + r, fill=theme.FAINT, outline="", tags=grab)

        btn = s(theme.SQUARE)
        down_x = x0 + width - 1 - s(12) - btn
        up_x = down_x - s(8) - btn
        last = len(self.order) - 1
        for name, bx, off in (("up", up_x, i == 0), ("down", down_x, i == last)):
            face = gfx.button(btn, btn, "toolbar", "disabled" if off else "normal", name)
            if face is not None:
                tags = ("push", f"{name}:{i}", f"tip_{name}", row_tag) if not off else (row_tag,)
                cv.create_image(bx, mid - btn / 2, image=face, anchor="nw", tags=tags)

        text_x = gx + s(14) + s(12)
        room = up_x - s(12) - text_x
        name_font = theme.fpx(theme.SANS, 20)
        cap_font = theme.fpx(theme.SANS, 15)
        block = line_height(name_font) + line_height(cap_font)
        top = mid - block / 2
        cv.create_text(text_x, top, text=fit_text(team.name, name_font, room), anchor="nw", fill=theme.TEXT,
                       font=name_font, tags=grab)
        cv.create_text(text_x, top + line_height(name_font), anchor="nw", fill=theme.DIM, font=cap_font, tags=grab,
                       text=fit_text(text.t("Captain Line", name=team.captain.twitch), cap_font, room))

    def _move(self, index, delta):
        """Moves a team up or down one spot (the arrow buttons)."""
        j = index + delta
        if 0 <= j < len(self.order):
            B.move_item(self.order, index, j)
            self._draw_order_row(index)
            self._draw_order_row(j)

    # ---------- drag and drop ----------

    def _on_press(self, event):
        """A press on a row starts a drag; a press on an arrow button moves that team one spot."""
        cv = self.seeds.canvas
        items = cv.find_withtag("current")
        if not items:
            return
        tags = cv.gettags(items[0])
        for tag in tags:
            if tag.startswith("up:") or tag.startswith("down:"):
                kind, _sep, idx = tag.partition(":")
                self._move(int(idx), -1 if kind == "up" else 1)
                return
        for tag in tags:
            if tag.startswith("row:"):
                self._drag_start(int(tag[4:]))
                return

    def _drag_start(self, index):
        """Starts dragging the row you pressed on."""
        self._drag_index = index
        self._draw_order_row(index)

    def _index_at(self, canvas_y):
        """Works out which row the mouse is over, staying inside the list."""
        index = int(canvas_y // self._row_step())
        return max(0, min(len(self.order) - 1, index))

    def _drag_motion(self, event):
        """While dragging, swaps the team into whichever row the mouse is over."""
        if self._drag_index is None or not self.order:
            return
        target = self._index_at(self.seeds.canvas.canvasy(event.y))
        old = self._drag_index
        if target != old:
            B.move_item(self.order, old, target)
            self._drag_index = target
            for i in range(min(old, target), max(old, target) + 1):
                self._draw_order_row(i)

    def _drag_end(self, event):
        """Lets go of the dragged row."""
        index = self._drag_index
        self._drag_index = None
        if index is not None:
            self._draw_order_row(index)

    # ---------- footer actions ----------

    def _on_confirm(self):
        """Builds the bracket in the chosen format and opens the bracket screen."""
        if len(self.order) < 2:
            return
        if self.selected_format == "single":
            data = B.build_single_bracket(self.order)
        elif self.selected_format == "double":
            data = B.build_double_bracket(self.order)
        else:
            data = B.build_league(self.order)
        self.app.bracket = data
        self.app.show_screen("bracket")

    def _on_save(self):
        """Saves the current settings to the save file and says so."""
        save_state(serialize_app_state(self.app), status="Bracket Setting")
        dialogs.notify_saved(self.app)

    def _on_back(self):
        """Goes back to Mystery Hero, or to Tournament Type if Mystery Hero was skipped."""
        origin = getattr(self.app, "bracket_settings_origin", None)
        self.app.show_screen("tournament_type" if origin == "tournament_type" else "mystery_spin")

    # ---------- hand-over for a light/dark switch ----------

    def capture_state(self):
        """Remembers where the seed list is scrolled to."""
        return {"scroll": self.seeds.canvas.yview()[0]}

    def restore_state(self, state):
        """Scrolls the seed list back to where it was."""
        self.seeds.canvas.yview_moveto(state.get("scroll", 0))
