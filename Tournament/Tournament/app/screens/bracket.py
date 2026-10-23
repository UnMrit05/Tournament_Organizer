"""Screen 5 - the bracket. Draws the tournament tree (or the league match list and standings) and lets the host click winners in."""

import tkinter as tk

from app.data import bracket as B
from app.ui import gfx, kit, text, theme
from app.ui.popup import show_captain_popup
from app.ui.stage import Stage
from app.ui.widgets import GlassButton, ToolButton, fit_text, line_height, text_width

ZOOM_MIN = 0.35
ZOOM_MAX = 2.5
ZOOM_STEP = 0.1
DEFAULT_ZOOM = 1.0
BASE_BOX_W = 264
BASE_BOX_H = 66
BASE_COL_GAP = 72
BASE_ROW_GAP = 34
SECTION_GAP = 56
SECTION_LABEL_H = 28
ROUND_LABEL_H = 28
PAD = 24
TOP_MARGIN = 20
SEED_W = 32
CHAMP_W = 176
CHAMP_H = 90
# How long a single click waits before its popup actually opens, so a
# following double-click (whose first press is itself a Button-1 event)
# can cancel it. Comfortably longer than a typical OS double-click window.
DOUBLE_CLICK_MS = 400

FORMAT_NAME_KEYS = {"single": "Single Elimination Name", "double": "Double Elimination Name",
                    "league": "League Name"}


class BracketScreen(Stage):
    """The bracket page: tournament tree, or league match list plus standings."""

    STEP = 4
    WATERMARK = "center"

    def __init__(self, parent, app):
        """Sets up the heading, footer and either the tree canvas or the league match list and standings."""
        super().__init__(parent, app, "bracket")
        self.data = app.bracket
        self.zoom = DEFAULT_ZOOM
        self._fitted = False
        self._user_zoomed = False
        self._pending_popup_id = None
        self._config_job = None
        self._view = (0, 0)
        self._images = []
        self._tag_count = 0
        self._content = (0, 0)
        self._rr_sig = {}
        self._rr_matches = []
        self._remaining_text = ""
        self._stand_sig = None
        self._rr_mode = self.data.format == "league" and not self.data.playoff_started

        kind = text.t(FORMAT_NAME_KEYS.get(self.data.format, "Single Elimination Name"))
        self.set_title(text.t("Bracket Heading", type=kind))

        self._build_footer()
        if self._rr_mode:
            self._build_rr_ui()
        else:
            self._build_tree_ui()
        self._refresh()

    # ---------- skeleton ----------

    def _build_footer(self):
        """The bottom row: Back on the left and End Tournament (only enabled once there's a champion) on the right."""
        footer_y = lambda: self.footer_top()
        h = theme.S(theme.FOOTER_H)
        back = GlassButton(self, text.t("Button Back"), lambda: self.app.show_screen("bracket_settings"),
                           kind="secondary")
        self.end_btn = GlassButton(self, text.t("End Tournament Button"), self._on_end, kind="primary")
        self.put(back, lambda: (self.footer_left(), footer_y(), back.pixel_width, h))
        self.put(self.end_btn, lambda: (self.right_edge() - self.end_btn.pixel_width, footer_y(),
                                        self.end_btn.pixel_width, h))

    def _build_tree_ui(self):
        """The tree view: an info row on top, the bracket canvas in a panel, and the zoom row below it."""
        info_h = theme.S(32)
        zoom_h = theme.S(32)
        top = lambda: self.body_top()
        zoom_top = lambda: self.footer_top() - self.gutter() - zoom_h
        canvas_top = lambda: top() + info_h + self.gutter()

        self._info_img = gfx.icon_alpha("info", theme.S(16), theme.ACCENT_TEXT)
        self._info_item = self.create_image(0, 0, anchor="w", image=self._info_img) if self._info_img else None
        self._hint_item = self.text_note("", self._hint_rect, color=theme.DIM, font=theme.fpx(theme.SANS, 17))
        self._prog_text = self.create_text(0, 0, anchor="e", text="", fill=theme.DIM, font=theme.fpx(theme.SANS, 17))
        self._prog_track = self.create_rectangle(0, 0, 1, 1, fill=theme.TRACK, outline="")
        self._prog_fill = self.create_rectangle(0, 0, 1, 1, fill=theme.ACCENT, outline="")
        self._progress = (0, 1)
        self.hook(self._place_progress)

        panel = self.draw_panel(lambda: (self.col_x(0), canvas_top(), self.span_w(12),
                                         zoom_top() - self.gutter() - canvas_top()))
        self.canvas = tk.Canvas(self, bg=theme.PANEL, highlightthickness=0, bd=0)
        self.canvas.bind("<ButtonPress-1>", self._pan_start, add="+")
        self.canvas.bind("<B1-Motion>", self._pan_move, add="+")
        self.canvas.bind("<MouseWheel>", lambda e: self._wheel(e, "y"))
        self.canvas.bind("<Shift-MouseWheel>", lambda e: self._wheel(e, "x"))
        self._panning = False
        self.put(self.canvas, panel, on_rect=self._set_view)

        self._zoom_out = ToolButton(self, "minus", lambda: self._zoom_by(-ZOOM_STEP), tip=text.t("Tip Zoom Out"))
        self._zoom_in = ToolButton(self, "plus", lambda: self._zoom_by(ZOOM_STEP), tip=text.t("Tip Zoom In"))
        self._zoom_item = self.create_text(0, 0, text="100%", fill=theme.DIM, font=theme.fpx(theme.SEMIBOLD, 12))
        side = theme.S(theme.SQUARE)
        gap = theme.S(12)
        label_w = theme.S(56)
        cx = lambda: self._size[0] / 2
        self.put(self._zoom_out, lambda: (cx() - label_w / 2 - gap - side, zoom_top(), side, side))
        self.put(self._zoom_in, lambda: (cx() + label_w / 2 + gap, zoom_top(), side, side))
        self.hook(lambda: self.coords(self._zoom_item, cx(), zoom_top() + side / 2))

    def _hint_rect(self):
        """Where the one-line hint sits in the info row (right of the info icon, left of the progress bar)."""
        x = self.col_x(0) + theme.S(24)
        right = self._size[0] - self.margin() - theme.S(120) - theme.S(12) - self._prog_width() - theme.S(24)
        return (x, self.body_top() + theme.S(16), right - x)

    def _prog_width(self):
        """How wide the 'n of m matches decided' words are."""
        return text_width(theme.fpx(theme.SANS, 17), self.itemcget(self._prog_text, "text"))

    def _place_progress(self):
        """Puts the info icon, the progress words and the progress bar in the info row."""
        mid = self.body_top() + theme.S(16)
        if self._info_item is not None:
            self.coords(self._info_item, self.col_x(0), mid)
        bar_w, bar_h = theme.S(120), theme.S(8)
        right = self._size[0] - self.margin()
        self.coords(self._prog_track, right - bar_w, mid - bar_h / 2, right, mid + bar_h / 2)
        done, total = self._progress
        fill_w = bar_w * (done / total) if total else 0
        self.coords(self._prog_fill, right - bar_w, mid - bar_h / 2, right - bar_w + fill_w, mid + bar_h / 2)
        self.coords(self._prog_text, right - bar_w - theme.S(12), mid)

    # ---------- top-level refresh ----------

    def _team_index(self, team):
        """Where the team sits in the draft order (decides its color)."""
        teams = self.app.teams
        for i, t in enumerate(teams):
            if t is team:
                return i
        return 0

    def _refresh(self):
        """Redraws whatever should be showing right now and updates the status line, progress and End button."""
        complete = B.is_tournament_complete(self.data)
        if self._rr_mode:
            self._update_rr()
        else:
            if self._view[0] >= 60:
                self._render_canvas()
                if not self._user_zoomed:
                    self._shrink_to_fit()
            self._update_info(complete)
        self.end_btn.configure(state="normal" if complete else "disabled")

    def _update_info(self, complete):
        """Updates the hint line and the 'n of m matches decided' progress in the tree view."""
        real = [m for m in self.data.matches.values() if m.bracket != "RR" and m.is_real_game]
        done = sum(1 for m in real if m.winner is not None)
        self._progress = (done, len(real))
        self.itemconfigure(self._prog_text, text=text.t("Matches Decided", done=done, total=len(real)))
        if complete and self.data.champion is not None:
            self.itemconfigure(self._hint_item, fill=theme.ACCENT_TEXT)
            self.set_note(self._hint_item, text.t("Champion Line", name=self.data.champion.name))
        else:
            self.itemconfigure(self._hint_item, fill=theme.DIM)
            self.set_note(self._hint_item, text.t("Bracket Hint"))
        self.relayout()

    def _record(self, match, team):
        """Marks a team as the winner of a match, then refreshes the page."""
        B.record_winner(match, team, self.data.matches)
        B.refresh_champion(self.data)
        self._refresh()

    def _undo(self, match):
        """Undoes a match's result, then refreshes the page."""
        B.undo_winner(match, self.data.matches)
        B.refresh_champion(self.data)
        self._refresh()

    def _toggle_match(self, match, team, is_winner):
        """Double-click handler: undoes the result if this team already won, otherwise makes them the winner."""
        # The first click of this double-click already queued a popup -
        # make sure it never opens, since a double-click should only toggle.
        self._cancel_pending_popup()
        if is_winner:
            self._undo(match)
        else:
            self._record(match, team)

    def _show_popup(self, event, team):
        """Queues the captain popup after a short wait, so a double-click can cancel it before it shows."""
        self._cancel_pending_popup()
        x_root, y_root = event.x_root, event.y_root
        self._pending_popup_id = self.after(
            DOUBLE_CLICK_MS, lambda: self._do_show_popup(x_root, y_root, team))

    def _do_show_popup(self, x_root, y_root, team):
        """Actually opens the captain popup once the wait is over."""
        self._pending_popup_id = None
        show_captain_popup(self, x_root, y_root, team)

    def _cancel_pending_popup(self):
        """Cancels a queued captain popup if there is one."""
        if self._pending_popup_id is not None:
            try:
                self.after_cancel(self._pending_popup_id)
            except Exception:
                pass
            self._pending_popup_id = None

    def _on_end(self):
        """Goes to the finish screen, but only if the tournament has a champion."""
        if B.is_tournament_complete(self.data):
            self.app.show_screen("congrats")

    def destroy(self):
        """Cancels any waiting popup or redraw before the screen goes away."""
        self._cancel_pending_popup()
        if self._config_job is not None:
            try:
                self.after_cancel(self._config_job)
            except Exception:
                pass
            self._config_job = None
        super().destroy()

    # ---------- hand-over for a light/dark switch ----------

    def capture_state(self):
        """Remembers the zoom level."""
        return {"zoom": self.zoom}

    def restore_state(self, state):
        """Puts the zoom level back (and skips the fit-to-window step)."""
        if "zoom" in state and not self._rr_mode:
            self.zoom = state["zoom"]
            self._fitted = True
            self._render_canvas()

    # ---------- zoom ----------

    def _zoom_by(self, delta):
        """Changes the zoom a bit (within the limits) and redraws the tree."""
        self.zoom = max(ZOOM_MIN, min(ZOOM_MAX, round(self.zoom + delta, 2)))
        self._user_zoomed = True
        if not self._rr_mode:
            self._render_canvas()

    def _set_view(self, width, height):
        """The tree's canvas got its size (before anything shows): fit the tree the first time, and redraw it
        a moment after the last size change on later ones."""
        self._view = (width, height)
        if width < 60 or height < 60:
            return
        if not self._fitted:
            self._fitted = True
            self._fit_zoom()
            return
        if self._config_job is not None:
            self.after_cancel(self._config_job)
        self._config_job = self.after(40, self._after_configure)

    def _after_configure(self):
        """Redraws the tree once a size change has settled."""
        self._config_job = None
        self._render_canvas()

    def _fit_zoom(self):
        """Starts at 100% and zooms out just enough that the whole tree fits the canvas."""
        self.zoom = DEFAULT_ZOOM
        self._render_canvas()
        self._shrink_to_fit()

    def _shrink_to_fit(self):
        """If the drawing is bigger than the canvas, zooms out (in 5% steps) until it fits. Never zooms in."""
        need_w, need_h = self._content
        have_w, have_h = self._view
        if have_w < 60 or have_h < 60 or (need_w <= have_w and need_h <= have_h):
            return
        factor = min(have_w / max(1, need_w), have_h / max(1, need_h))
        shrunk = max(ZOOM_MIN, int(self.zoom * factor * 20) / 20)
        if shrunk < self.zoom:
            self.zoom = shrunk
            self._render_canvas()

    def _pan_start(self, event):
        """Starts dragging the view, but only when the press landed on empty canvas (not on a team)."""
        self._panning = not self.canvas.find_withtag("current")
        if self._panning:
            self.canvas.scan_mark(event.x, event.y)

    def _pan_move(self, event):
        """Drags the view along with the mouse."""
        if self._panning:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _wheel(self, event, axis):
        """Scrolls the tree with the mouse wheel (hold Shift to go sideways)."""
        step = int(-1 * (event.delta / 120))
        if axis == "y":
            self.canvas.yview_scroll(step, "units")
        else:
            self.canvas.xview_scroll(step, "units")

    # ---------- league: round robin (drawn on canvases, updated in place) ----------

    def _build_rr_ui(self):
        """Sets up the league's round robin match list (left) and the standings panel (right)."""
        top = lambda: self.body_top()
        list_top = lambda: top() + theme.S(44)
        list_h = lambda: self.body_bottom() - list_top()
        pad = theme.S(12)
        self._rr_matches = sorted((m for m in self.data.matches.values() if m.bracket == "RR"), key=lambda m: m.id)

        self.section(text.t("Round Robin Label"), lambda: (self.col_x(0), top(), self.span_w(7)),
                     reserve=self._chip_width)
        self.hook(self._draw_remaining_chip)
        left = self.draw_panel(lambda: (self.col_x(0), list_top(), self.span_w(7), list_h()))
        hint_font = theme.fpx(theme.SANS, 17)
        hint_h = line_height(hint_font)
        self.text_note(text.t("Bracket Hint"),
                       lambda: (left()[0] + pad, left()[1] + pad + hint_h / 2, left()[2] - 2 * pad),
                       color=theme.DIM, font=hint_font)
        self.rr_scroll = kit.ScrollCanvas(self, theme.PANEL, on_size=self._draw_rr_cards)
        self.put(self.rr_scroll, lambda: (left()[0] + pad, left()[1] + 2 * pad + hint_h, left()[2] - 2 * pad,
                                          left()[3] - 3 * pad - hint_h), on_rect=self.rr_scroll.fit)
        cv = self.rr_scroll.canvas
        for m in self._rr_matches:
            for side in ("a", "b"):
                tag = f"mrow:{m.id}:{side}"
                cv.tag_bind(tag, "<Button-1>", lambda e, mm=m, sd=side: self._rr_click(e, mm, sd))
                cv.tag_bind(tag, "<Double-Button-1>", lambda e, mm=m, sd=side: self._rr_double(mm, sd))
                cv.tag_bind(tag, "<Enter>", lambda e: cv.configure(cursor="hand2"))
                cv.tag_bind(tag, "<Leave>", lambda e: cv.configure(cursor=""))

        self.section(text.t("Standings Label"), lambda: (self.col_x(7), top(), self.span_w(5)))
        self._stand_panel = self.draw_panel(lambda: (self.col_x(7), list_top(), self.span_w(5), list_h()))
        self._build_standings()

    def _chip_font(self):
        """The font of the 'n remaining' chip."""
        return theme.fpx(theme.SANS, 15)

    def _chip_width(self):
        """How wide the 'n remaining' chip is (the section line leaves room for it)."""
        return kit.chip_width(self._remaining_text, self._chip_font())

    def _draw_remaining_chip(self):
        """Draws the 'n matches remaining' chip at the right end of the Round Robin title row."""
        if self._size[0] < 10:
            return
        self.delete("rrchip")
        width = self._chip_width()
        x = self.col_x(0) + self.span_w(7) - width
        kit.draw_chip(self, int(x), int(self.body_top()), self._remaining_text, self._chip_font(),
                      theme.mix(theme.BTN_TOP, theme.BTN_BOTTOM, 0.5), theme.BTN_EDGE, theme.TEXT, tags=("rrchip",))

    def _rr_card_geometry(self, index):
        """Where match card number `index` sits on the list canvas (two columns): (x, y, w, h)."""
        gap = theme.S(8)
        card_w = (self.rr_scroll.width - gap) // 2
        card_h = 2 + 2 * theme.S(32) + 1
        return ((index % 2) * (card_w + gap), (index // 2) * (card_h + gap), card_w, card_h)

    def _draw_rr_cards(self, width=None):
        """Draws every match card from scratch (the first time, and when the list gets a new width)."""
        if self.rr_scroll.width < 40:
            return
        self.rr_scroll.canvas.delete("all")
        self._rr_sig = {}
        for index, m in enumerate(self._rr_matches):
            self._draw_rr_card(m, index)
        rows = (len(self._rr_matches) + 1) // 2
        _x, _y, _w, card_h = self._rr_card_geometry(0)
        self.rr_scroll.set_content_height(max(0, rows * (card_h + theme.S(8)) - theme.S(8)))

    def _rr_signature(self, m):
        """Boils a match down to what its card shows, so unchanged cards are left alone."""
        return (self.rr_scroll.width, m.winner is not None, id(m.winner), id(m.team_a), id(m.team_b),
                theme.MODE, theme.ACCENT)

    def _draw_rr_card(self, m, index):
        """Draws one match card: a number box and two team rows (colored square, name, tick)."""
        s = theme.S
        cv = self.rr_scroll.canvas
        signature = self._rr_signature(m)
        if self._rr_sig.get(m.id) == signature:
            return
        self._rr_sig[m.id] = signature
        cv.delete(f"mc:{m.id}")
        x, y, w, h = self._rr_card_geometry(index)
        decided = m.winner is not None
        base = ("mc:" + str(m.id),)
        edge = theme.LINE if decided else theme.mix(theme.LINE, theme.FAINT, 0.4)
        kit.box(cv, x, y, x + w, y + h, theme.PANEL_2, edge, base)
        seed_w = s(SEED_W)
        cv.create_rectangle(x + 1, y + 1, x + 1 + seed_w, y + h - 1, fill=theme.ROW, outline="", tags=base)
        cv.create_text(x + 1 + seed_w / 2, y + h / 2, text=str(index + 1), fill=theme.DIM,
                       font=theme.fpx(theme.SEMIBOLD, 11), tags=base)
        line_h = s(32)
        name_font_flags = {True: ("overstrike",), False: ()}
        for k, side in enumerate(("a", "b")):
            team = m.team_a if side == "a" else m.team_b
            if team is None:
                continue
            tags = base + (f"mrow:{m.id}:{side}",)
            ry = y + 1 + k * (line_h + 1)
            is_winner = m.winner is team
            is_loser = decided and not is_winner
            h1, _h2 = theme.team_hue(self._team_index(team))
            bg = theme.mix(theme.PANEL_2, h1, 0.42 if is_winner else 0.18)
            cv.create_rectangle(x + 1 + seed_w, ry, x + w - 1, ry + line_h, fill=bg, outline="", tags=tags)
            dot_x = x + 1 + seed_w + s(8)
            cv.create_rectangle(dot_x, ry + line_h / 2 - s(6), dot_x + s(12), ry + line_h / 2 + s(6),
                                fill=theme.mix(bg, h1, 0.45) if is_loser else h1, outline="", tags=tags)
            right = x + w - 1 - s(8)
            if is_winner:
                icon = gfx.icon_alpha("check", s(16), theme.TEXT)
                self._images.append(icon)
                if icon is not None:
                    cv.create_image(right, ry + line_h / 2, image=icon, anchor="e", tags=tags)
                right -= s(16) + s(8)
            font = theme.fpx(theme.SANS, 17, *name_font_flags[is_loser])
            name_x = dot_x + s(12) + s(8)
            cv.create_text(name_x, ry + line_h / 2, text=fit_text(team.name, font, right - name_x), anchor="w",
                           fill=theme.DIM if is_loser else theme.TEXT, font=font, tags=tags)
            if k == 0:
                cv.create_rectangle(x + 1 + seed_w, ry + line_h, x + w - 1, ry + line_h + 1, fill=theme.ROW_EDGE,
                                    outline="", tags=base)

    def _rr_click(self, event, match, side):
        """Single click on a team in the match list: shows its captain after a moment."""
        team = match.team_a if side == "a" else match.team_b
        if team is not None:
            self._show_popup(event, team)

    def _rr_double(self, match, side):
        """Double click on a team in the match list: marks the win, or undoes it."""
        team = match.team_a if side == "a" else match.team_b
        if team is None:
            return
        is_winner = match.winner is team
        if match.winner is None or is_winner:
            self._toggle_match(match, team, is_winner)
        else:
            self._cancel_pending_popup()

    def _build_standings(self):
        """The standings panel: the table is drawn by _draw_standings; the Generate Playoffs button and its hint sit at the bottom."""
        total = sum(1 for m in self.data.matches.values() if m.bracket == "RR")
        pad = theme.S(12)
        self._hint_font = theme.fpx(theme.SANS, 16)
        self._unlock_text = text.t("Unlocks Hint", n=total)
        self.generate_btn = GlassButton(self, text.t("Generate Playoffs Button"), self._start_playoffs, kind="primary")
        btn_h = theme.S(theme.FOOTER_H)
        self._gen_rect = lambda: (self._stand_panel()[0] + pad,
                                  self._stand_panel()[1] + self._stand_panel()[3] - pad - self._bottom_h(),
                                  self._stand_panel()[2] - 2 * pad, btn_h)
        self.put(self.generate_btn, self._gen_rect, on_rect=lambda w, h: self.generate_btn.resize_to(w))
        self._unlock_item = self.create_text(0, 0, anchor="nw", text=self._unlock_text, fill=theme.DIM,
                                             font=self._hint_font)
        self.hook(self._place_unlock)
        self.hook(self._draw_standings)

    def _bottom_h(self):
        """How tall the bottom block of the standings panel is (button, gap and the wrapped hint)."""
        room_w = self._stand_panel()[2] - 2 * theme.S(12)
        self.itemconfigure(self._unlock_item, width=max(120, int(room_w)))
        box = self.bbox(self._unlock_item)
        hint_h = (box[3] - box[1]) if box else line_height(self._hint_font)
        return theme.S(theme.FOOTER_H) + theme.S(8) + hint_h

    def _place_unlock(self):
        """Puts the 'Unlocks once all n matches are decided' hint under the Generate Playoffs button."""
        if self._size[0] < 10:
            return
        x, y, w, h = self._gen_rect()
        self.itemconfigure(self._unlock_item, width=max(120, int(w)))
        self.coords(self._unlock_item, x, y + h + theme.S(8))

    def _draw_standings(self):
        """Draws the standings table: rank, team, win-loss and a little win bar, with a dashed line under the cut-off."""
        if self._size[0] < 10:
            return
        standings = B.league_standings(self.data)
        x, y, w, _h = self._stand_panel()
        signature = (self._size, theme.MODE, theme.ACCENT,
                     tuple((id(team), wins, played) for team, wins, played in standings))
        if signature == self._stand_sig:
            return
        self._stand_sig = signature
        self.delete("stand")
        s = theme.S
        tags = ("stand",)
        pad = s(12)
        left, right = x + pad, x + w - pad
        row_h = s(40)
        cut = min(4, len(standings))
        cy = y + pad
        name_font = theme.fpx(theme.SANS, 18)
        record_font = theme.fpx(theme.SEMIBOLD, 13)
        rank_font = theme.fpx(theme.SEMIBOLD, 12)
        record_w = text_width(record_font, "00–00")
        for i, (team, wins, played) in enumerate(standings):
            h1, h2 = theme.team_hue(self._team_index(team))
            out = i >= cut
            bg = theme.mix(theme.PANEL, h1, 0.16)
            self.create_rectangle(left, cy, right, cy + row_h, fill=bg, outline="", tags=tags)
            face_top = theme.mix(theme.PANEL, h1, 0.5) if out else h1
            face_bottom = theme.mix(theme.PANEL, h2, 0.5) if out else h2
            side = s(28)
            rx = left + s(12)
            face = gfx.vertical_swatch(side, side, [(0, face_top), (1, face_bottom)])
            if face is not None:
                self._stand_imgs = getattr(self, "_stand_imgs", [])
                self._stand_imgs.append(face)
                self.create_image(rx, cy + (row_h - side) / 2, image=face, anchor="nw", tags=tags)
            else:
                self.create_rectangle(rx, cy + (row_h - side) / 2, rx + side, cy + (row_h + side) / 2, fill=h1,
                                      outline="", tags=tags)
            self.create_text(rx + side / 2, cy + row_h / 2, text=str(i + 1), fill=theme.HEADER_INK, font=rank_font, tags=tags)
            bar_w, bar_h = s(64), s(6)
            bar_x = right - s(16) - bar_w
            self.create_rectangle(bar_x, cy + (row_h - bar_h) / 2, bar_x + bar_w, cy + (row_h + bar_h) / 2,
                                  fill=theme.TRACK, outline="", tags=tags)
            pct = (wins / played) if played else 0
            if pct > 0:
                self.create_rectangle(bar_x, cy + (row_h - bar_h) / 2, bar_x + bar_w * pct, cy + (row_h + bar_h) / 2,
                                      fill=h1, outline="", tags=tags)
            rec_right = bar_x - s(12)
            self.create_text(rec_right, cy + row_h / 2, text=f"{wins}–{played - wins}", anchor="e", fill=theme.DIM,
                             font=record_font, tags=tags)
            name_x = rx + side + s(12)
            self.create_text(name_x, cy + row_h / 2, text=fit_text(team.name, name_font, rec_right - record_w - s(8) - name_x),
                             anchor="w", fill=theme.TEXT, font=name_font, tags=tags)
            cy += row_h
            if i == cut - 1 and len(standings) > cut:
                self._draw_cut_line(left, right, cy, tags, cut)
                cy += s(24)

    def _draw_cut_line(self, left, right, y, tags, cut):
        """The dashed 'Top 4 advance to playoffs' divider between the cut-off rows."""
        s = theme.S
        words = text.t("Advance Line", n=cut).upper()
        font = theme.fpx(theme.SEMIBOLD, 11)
        mid = y + s(12)
        half = text_width(font, words) // 2 + s(12)
        pad = s(16)
        cx = (left + right) / 2
        self.create_line(left + pad, mid, max(left + pad, cx - half), mid, fill=theme.ACCENT_TEXT, dash=(4, 4), tags=tags)
        self.create_line(min(right - pad, cx + half), mid, right - pad, mid, fill=theme.ACCENT_TEXT, dash=(4, 4),
                         tags=tags)
        self.create_text(cx, mid, text=words, fill=theme.ACCENT_TEXT, font=font, tags=tags)

    def _update_rr(self):
        """Redraws only the match cards that changed, the standings table, the chip and the Generate Playoffs button."""
        for index, m in enumerate(self._rr_matches):
            self._draw_rr_card(m, index)
        remaining = sum(1 for m in self.data.matches.values() if m.bracket == "RR" and m.winner is None)
        self._remaining_text = text.t("Round Robin Remaining", n=remaining)
        self.generate_btn.configure(state="normal" if B.league_round_robin_complete(self.data) else "disabled")
        self.relayout()

    def _start_playoffs(self):
        """Builds the league playoff bracket and rebuilds the page as the tree view."""
        B.start_league_playoffs(self.data, playoff_size=min(4, len(self.data.seed_order)))
        self.app.show_screen("bracket")

    # ---------- single / double / playoff-stage: canvas tree ----------

    def _grouped_rounds(self, bracket_key):
        """Collects one bracket's matches into a list per round, in order."""
        by_round = {}
        for m in self.data.matches.values():
            if m.bracket == bracket_key:
                by_round.setdefault(m.round_index, []).append(m)
        return [sorted(by_round[r], key=lambda m: m.id) for r in sorted(by_round)]

    @staticmethod
    def _revealed(m):
        """Says whether a match is worth drawing yet (a team has reached it or it's decided)."""
        return m.team_a is not None or m.team_b is not None or m.winner is not None

    def _compute_y(self, rounds, box_h, row_gap):
        """Works out how far down each match box sits, putting later matches between the ones that feed them."""
        y = {}
        if not rounds:
            return y
        step = box_h + row_gap
        for i, m in enumerate(rounds[0]):
            y[m.id] = i * step
        for r in range(1, len(rounds)):
            for m in rounds[r]:
                feeders = [fm for fm in rounds[r - 1] if fm.next_match_id == m.id]
                y[m.id] = (sum(y[f.id] for f in feeders) / len(feeders)) if feeders else 0
        return y

    def _px(self, ref_px):
        """A design size turned into real pixels at the current zoom (never less than 1)."""
        return max(1, int(round(ref_px * theme.SCALE * self.zoom)))

    def _font(self, family, ref_px, *flags):
        """A font for the tree at the current zoom (can get very small when zoomed far out)."""
        return (family, -max(6, self._px(ref_px))) + tuple(flags)

    def _render_canvas(self):
        """Clears and redraws the whole tree: winners, losers, playoffs and the grand final."""
        cv = self.canvas
        left, top_edge = cv.xview()[0], cv.yview()[0]
        cv.delete("all")
        self._images = []
        self._tag_count = 0
        s = theme.SCALE * self.zoom
        box_w, box_h = BASE_BOX_W * s, BASE_BOX_H * s
        col_gap, row_gap = BASE_COL_GAP * s, BASE_ROW_GAP * s
        section_gap = SECTION_GAP * s
        section_label_h = SECTION_LABEL_H * s
        round_label_h = ROUND_LABEL_H * s
        pad = PAD * s
        section_font = self._font(theme.SEMIBOLD, 13)
        round_font = self._font(theme.SEMIBOLD, 12)
        extent = {"x": 0, "y": 0}

        def grow(x, y):
            """Remembers how far right and down the drawing reaches."""
            extent["x"], extent["y"] = max(extent["x"], x), max(extent["y"], y)

        def draw_group(rounds, y_offset):
            """Draws one bracket section: round names, match boxes, then the lines between them."""
            matches_top = y_offset + round_label_h
            y = self._compute_y(rounds, box_h, row_gap)
            positions = {}
            for r, round_matches in enumerate(rounds):
                x = pad + r * (box_w + col_gap)
                visible_in_round = [m for m in round_matches if self._revealed(m)]
                if visible_in_round:
                    label = visible_in_round[0].label or text.t("Round Label", n=r + 1)
                    cv.create_text(x + 2, y_offset + 2, anchor="nw", text=label.upper(), fill=theme.DIM,
                                   font=round_font)
                for m in round_matches:
                    if not self._revealed(m):
                        continue
                    top = y[m.id] + matches_top
                    positions[m.id] = (x, top)
                    self._draw_match_box(m, x, top, box_w, box_h, s)
                    grow(x + box_w, top + box_h)
            for round_matches in rounds:
                for m in round_matches:
                    if m.id in positions and m.next_match_id and m.next_match_id in positions:
                        x0, y0 = positions[m.id]
                        x1, y1 = positions[m.next_match_id]
                        self._draw_connector(x0 + box_w, y0 + box_h / 2, x1, y1 + box_h / 2, col_gap,
                                             m.winner is not None, s)
            bottom = max((y[m.id] for rm in rounds for m in rm if m.id in positions), default=None)
            bottom = (bottom + matches_top + box_h) if bottom is not None else matches_top
            return positions, bottom

        y_cursor = TOP_MARGIN * s
        final_pos = None
        w_rounds = self._grouped_rounds("W")
        w_positions = {}
        if w_rounds:
            if self.data.format == "double":
                cv.create_text(pad + 2, y_cursor, anchor="nw", text=text.t("Winners Bracket Label").upper(),
                               fill=theme.TEXT, font=section_font)
                y_start = y_cursor + section_label_h
            else:
                y_start = y_cursor
            w_positions, bottom = draw_group(w_rounds, y_start)
            y_cursor = bottom + section_gap
            if self.data.format != "double" and w_rounds[-1] and w_rounds[-1][0].id in w_positions:
                final_pos = w_positions[w_rounds[-1][0].id]

        l_rounds = self._grouped_rounds("L")
        l_positions = {}
        if l_rounds and any(self._revealed(m) for rm in l_rounds for m in rm):
            cv.create_text(pad + 2, y_cursor, anchor="nw", text=text.t("Losers Bracket Label").upper(),
                           fill=theme.TEXT, font=section_font)
            l_positions, bottom = draw_group(l_rounds, y_cursor + section_label_h)
            y_cursor = bottom + section_gap

        p_rounds = self._grouped_rounds("P")
        if p_rounds:
            cv.create_text(pad + 2, y_cursor, anchor="nw", text=text.t("Playoffs Label").upper(),
                           fill=theme.TEXT, font=section_font)
            p_positions, bottom = draw_group(p_rounds, y_cursor + section_label_h)
            if p_rounds[-1] and p_rounds[-1][0].id in p_positions:
                final_pos = p_positions[p_rounds[-1][0].id]

        gf = self.data.matches.get("GF")
        if gf and self._revealed(gf):
            last_col = max(len(w_rounds), len(l_rounds))
            x = pad + last_col * (box_w + col_gap)
            w_final = w_rounds[-1][0] if w_rounds else None
            l_final = l_rounds[-1][0] if l_rounds else None
            ys = [pos[1] for pos in (w_positions.get(w_final.id) if w_final else None,
                                     l_positions.get(l_final.id) if l_final else None) if pos]
            top = (sum(ys) / len(ys)) if ys else 0
            cv.create_text(x + 2, top - section_label_h + 6, anchor="nw", text=text.t("Grand Final Label").upper(),
                           fill=theme.DIM, font=round_font)
            self._draw_match_box(gf, x, top, box_w, box_h, s)
            if w_final and w_final.id in w_positions:
                fx, fy = w_positions[w_final.id]
                self._draw_connector(fx + box_w, fy + box_h / 2, x, top + box_h / 2, col_gap,
                                     w_final.winner is not None, s)
            if l_final and l_final.id in l_positions:
                fx, fy = l_positions[l_final.id]
                self._draw_connector(fx + box_w, fy + box_h / 2, x, top + box_h / 2, col_gap,
                                     l_final.winner is not None, s)
            grow(x + box_w, top + box_h)
            final_pos = (x, top)

        if final_pos is not None:
            fx, fy = final_pos
            cx = fx + box_w + col_gap
            cy = fy + box_h / 2
            line_w = max(1, self._px(1.6))
            cv.create_line(fx + box_w, cy, cx, cy, fill=theme.FAINT, width=line_w, dash=(4, 5))
            self._draw_champion_slot(cx, cy - CHAMP_H * s / 2, CHAMP_W * s, CHAMP_H * s, s)
            grow(cx + CHAMP_W * s, cy + CHAMP_H * s / 2)

        self._content = (extent["x"] + pad, extent["y"] + pad)
        view_w, view_h = self._view
        cv.configure(scrollregion=(0, 0, max(view_w, self._content[0]), max(view_h, self._content[1])))
        cv.xview_moveto(left)
        cv.yview_moveto(top_edge)
        self.itemconfigure(self._zoom_item, text=f"{int(round(self.zoom * 100))}%")

    def _draw_champion_slot(self, x, y, w, h, s):
        """The dashed 'champion' box at the end of the tree: a trophy and TBD, or the winning team once decided."""
        cv = self.canvas
        champion = self.data.champion
        size = self._px(24)
        if champion is None:
            cv.create_rectangle(x, y, x + w, y + h, outline=theme.FAINT, dash=(4, 5), width=1)
            color, label, fg = theme.FAINT, text.t("Slot TBD").upper(), theme.DIM
        else:
            h1, h2 = theme.team_hue(self._team_index(champion))
            face = gfx.vertical_swatch(max(1, int(w) - 2), max(1, int(h) - 2),
                                       [(0, theme.mix(theme.PANEL, h1, 0.45)), (1, theme.mix(theme.PANEL, h2, 0.15))])
            if face is not None:
                self._images.append(face)
                cv.create_image(x + 1, y + 1, image=face, anchor="nw")
            cv.create_rectangle(x, y, x + w, y + h, outline=theme.ACCENT_TEXT, width=2)
            color, label, fg = theme.ACCENT_TEXT, fit_text(champion.name, self._font(theme.SANS, 17), w - 16 * s), theme.TEXT
        icon = gfx.icon_alpha("trophy", size, color)
        if icon is not None:
            self._images.append(icon)
            cv.create_image(x + w / 2, y + h * 0.34, image=icon)
        cv.create_text(x + w / 2, y + h * 0.72, text=label, fill=fg,
                       font=self._font(theme.SEMIBOLD if champion is None else theme.SANS,
                                       12 if champion is None else 17))

    def _seed_of(self, team):
        """The team's seed number (1 = top seed), or blank when it isn't in the seed list."""
        for i, t in enumerate(self.data.seed_order):
            if t is team:
                return str(i + 1)
        return ""

    def _draw_match_box(self, m, x, top, box_w, box_h, s):
        """Draws one match box with both team rows, and hooks up the click and double-click."""
        cv = self.canvas
        live = m.team_a is not None and m.team_b is not None and m.winner is None
        cv.create_rectangle(x, top, x + box_w, top + box_h, fill=theme.PANEL_2,
                            outline=theme.ACCENT_TEXT if live else theme.LINE, width=2 if live else 1)
        half = box_h / 2
        for i, (side, team) in enumerate((("a", m.team_a), ("b", m.team_b))):
            self._draw_team_row(m, side, team, x, top + half * i, box_w, half, s)
        cv.create_line(x + 1, top + half, x + box_w - 1, top + half, fill=theme.ROW_EDGE)
        if m.auto:
            cv.create_text(x + box_w - 6 * s, top + 3 * s, anchor="ne", text=text.t("Bye Tag"), fill=theme.DIM,
                           font=self._font(theme.SANS, 11))

    def _draw_team_row(self, m, side, team, x, y, w, h, s):
        """Draws one team's half of a match box: seed block, name and a tick for the winner."""
        cv = self.canvas
        inset = 1
        seed_w = SEED_W * s
        text_x = x + seed_w + 8 * s
        if team is None:
            label = text.t("Slot Bye") if m.expected < 2 else text.t("Slot TBD")
            cv.create_rectangle(x + inset, y + inset, x + seed_w, y + h - inset, fill=theme.ROW, outline="")
            cv.create_text(text_x, y + h / 2, anchor="w", text=label, fill=theme.DIM,
                           font=self._font(theme.SANS, 17, "italic"))
            return
        is_winner = m.winner is team
        is_loser = m.winner is not None and not is_winner
        h1, h2 = theme.team_hue(self._team_index(team))
        self._tag_count += 1
        tag = f"row{self._tag_count}"
        row_fill = theme.mix(theme.PANEL_2, h1, 0.40) if is_winner else theme.PANEL_2
        cv.create_rectangle(x + inset, y + inset, x + w - inset, y + h - inset, fill=row_fill, outline="", tags=(tag,))
        top_c = theme.mix(theme.PANEL_2, h1, 0.45) if is_loser else h1
        bottom_c = theme.mix(theme.PANEL_2, h2, 0.45) if is_loser else h2
        face = gfx.vertical_swatch(max(1, int(seed_w) - inset), max(1, int(h) - 2 * inset),
                                   [(0, top_c), (1, bottom_c)])
        if face is not None:
            self._images.append(face)
            cv.create_image(x + inset, y + inset, image=face, anchor="nw", tags=(tag,))
        else:
            cv.create_rectangle(x + inset, y + inset, x + seed_w, y + h - inset, fill=top_c, outline="", tags=(tag,))
        cv.create_text(x + seed_w / 2, y + h / 2, text=self._seed_of(team), fill=theme.HEADER_INK,
                       font=self._font(theme.SEMIBOLD, 11), tags=(tag,))
        room = w - seed_w - 8 * s - (28 * s if is_winner else 8 * s)
        font = self._font(theme.SANS, 17)
        cv.create_text(text_x, y + h / 2, anchor="w", text=fit_text(team.name, font, room),
                       fill=theme.DIM if is_loser else theme.TEXT, font=font, tags=(tag,))
        if is_winner:
            cx, cy, r = x + w - 16 * s, y + h / 2, 5 * s
            cv.create_line(cx - r, cy, cx - r * 0.3, cy + r * 0.8, cx + r, cy - r * 0.8, fill=theme.TEXT,
                           width=max(2, self._px(2)), tags=(tag,))
        cv.tag_bind(tag, "<Button-1>", lambda e, t=team: self._show_popup(e, t))
        toggleable = ((m.winner is None and m.team_a is not None and m.team_b is not None)
                      or (is_winner and not m.auto))
        if toggleable:
            cv.tag_bind(tag, "<Double-Button-1>",
                        lambda e, mm=m, t=team, win=is_winner: self._toggle_match(mm, t, win))
        cv.tag_bind(tag, "<Enter>", lambda e: cv.configure(cursor="hand2"))
        cv.tag_bind(tag, "<Leave>", lambda e: cv.configure(cursor="arrow"))

    def _draw_connector(self, x0, y0, x1, y1, col_gap, on, s):
        """Draws the elbow line from one match box over to the next (accent colored once the first match is decided)."""
        mid = x0 + col_gap / 2
        color = theme.ACCENT_TEXT if on else theme.FAINT
        self.canvas.create_line(x0, y0, mid, y0, mid, y1, x1, y1, fill=color, width=max(1, self._px(1.6)))
