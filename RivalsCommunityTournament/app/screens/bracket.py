"""Screen 6 - Bracket.

Single/double elimination (and a league's playoff stage) render as a
zoomable, scrollable canvas tree. Only a team's actual starting
position is shown up front; a later round's box only appears once a
team has actually arrived there (v0.26 item 5) - this also means the
per-column round label ("Round 1", "Quarterfinal", ...) and each
bracket section's own title ("Winners Bracket", "Losers Bracket") are
drawn in two clearly separate rows so they never overlap (item 6).

Click a team in an undecided match to mark them the winner, which
propagates automatically (winner into the next round, and for double
elimination the loser into the losers bracket) via app.data.bracket.
Click an already-decided match's winner to undo that result and
everything that depended on it (item 8) - not available for an
auto-resolved bye, since there is nothing to undo.

A league's round-robin stage renders as a plain match list + live
standings until every match is decided, at which point "Generate
Playoffs" builds the playoff bracket. The match list's rows are built
once and only updated in place afterwards, so marking a winner never
rebuilds the list or resets its scroll position (item 7).
"""

import tkinter as tk

from app.data import bracket as B
from app.ui import theme
from app.ui.scrollable import ScrollableFrame

ZOOM_LEVELS = [0.75, 1.0, 1.25, 1.5]
DEFAULT_ZOOM_INDEX = 1
BASE_BOX_W = 170
BASE_BOX_H = 56
BASE_COL_GAP = 90
BASE_ROW_GAP = 22
SECTION_GAP = 70
SECTION_LABEL_H = 24
ROUND_LABEL_H = 22


class BracketScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.data = app.bracket
        self.zoom_index = DEFAULT_ZOOM_INDEX

        self._rr_built = False
        self._rr_row_refs = {}

        # ---- footer packed first so it reliably keeps its space ----
        footer = tk.Frame(self, bg=theme.BG)
        footer.pack(side="bottom", fill="x", padx=20, pady=14)
        tk.Button(footer, text="Back", command=lambda: app.show_screen("bracket_settings"),
                   **theme.button_kwargs()).pack(side="left")
        self.end_btn = tk.Button(footer, text="End Tournament", command=self._on_end,
                                   **theme.primary_button_kwargs())
        self.end_btn.pack(side="right")

        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill="x", padx=20, pady=(16, 6))
        title = {"single": "Bracket — Single Elimination",
                 "double": "Bracket — Double Elimination",
                 "league": "Bracket — League + Playoffs"}.get(self.data.format, "Bracket")
        tk.Label(header, text=title, fg=theme.TEXT, bg=theme.BG,
                  font=theme.FONT_HEADING).pack(side="left")
        zoom_row = tk.Frame(header, bg=theme.BG)
        zoom_row.pack(side="right")
        tk.Button(zoom_row, text="−", command=lambda: self._zoom(-1),
                   **theme.button_kwargs()).pack(side="left", padx=3)
        tk.Button(zoom_row, text="+", command=lambda: self._zoom(1),
                   **theme.button_kwargs()).pack(side="left", padx=3)

        self.status_lbl = tk.Label(self, fg=theme.DIM, bg=theme.BG, font=theme.FONT_SMALL)
        self.status_lbl.pack(anchor="w", padx=20)

        # ---- one of these two fills the remaining space, toggled in _refresh ----
        self.canvas_wrap = tk.Frame(self, bg=theme.BG)
        self.canvas_wrap.rowconfigure(0, weight=1)
        self.canvas_wrap.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.canvas_wrap, bg=theme.PANEL, highlightthickness=0)
        vbar = tk.Scrollbar(self.canvas_wrap, orient="vertical", command=self.canvas.yview)
        hbar = tk.Scrollbar(self.canvas_wrap, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")

        self.rr_wrap = tk.Frame(self, bg=theme.BG)

        self._refresh()

    # ---------- top-level refresh ----------

    def _refresh(self):
        is_rr_phase = (self.data.format == "league" and not self.data.playoff_started)
        if is_rr_phase:
            self.canvas_wrap.pack_forget()
            self.rr_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))
            if not self._rr_built:
                self._build_rr()
                self._rr_built = True
            self._update_rr()
        else:
            self.rr_wrap.pack_forget()
            self.canvas_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))
            self._render_canvas()

        complete = B.is_tournament_complete(self.data)
        self.end_btn.configure(state="normal" if complete else "disabled")
        if complete:
            self.status_lbl.configure(text=f"Champion: {self.data.champion.name}")
        elif is_rr_phase:
            remaining = sum(1 for m in self.data.matches.values()
                              if m.bracket == "RR" and m.winner is None)
            self.status_lbl.configure(text=f"Round robin: {remaining} match(es) remaining")
        else:
            self.status_lbl.configure(text="Click a team to mark them the winner. Click a winner to undo.")

    def _record(self, match, team):
        B.record_winner(match, team, self.data.matches)
        B.refresh_champion(self.data)
        self._refresh()

    def _undo(self, match):
        B.undo_winner(match, self.data.matches)
        B.refresh_champion(self.data)
        self._refresh()

    def _on_end(self):
        if B.is_tournament_complete(self.data):
            self.app.show_screen("congrats")

    def _zoom(self, delta):
        new_index = self.zoom_index + delta
        if 0 <= new_index < len(ZOOM_LEVELS):
            self.zoom_index = new_index
            if self.data.format != "league" or self.data.playoff_started:
                self._render_canvas()

    # ---------- league: round robin (built once) + standings (rebuilt; no scrollbar there) ----------

    def _build_rr(self):
        for w in self.rr_wrap.winfo_children():
            w.destroy()
        self._rr_row_refs = {}

        body = tk.Frame(self.rr_wrap, bg=theme.BG)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=6)
        body.columnconfigure(1, weight=4)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=theme.BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(left, text="Round robin matches", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))
        self.match_scroll = ScrollableFrame(left)
        self.match_scroll.pack(fill="both", expand=True)

        rr_matches = sorted((m for m in self.data.matches.values() if m.bracket == "RR"),
                              key=lambda m: m.id)
        for m in rr_matches:
            row = tk.Frame(self.match_scroll.body, bg=theme.PANEL_2, highlightbackground=theme.LINE,
                             highlightthickness=1)
            row.pack(fill="x", pady=4)
            lbl_a = tk.Label(row, bg=theme.PANEL_2, anchor="w", font=("Segoe UI Semibold", 11))
            lbl_a.pack(fill="x", padx=14, pady=(8, 2))
            lbl_b = tk.Label(row, bg=theme.PANEL_2, anchor="w", font=("Segoe UI Semibold", 11))
            lbl_b.pack(fill="x", padx=14, pady=(2, 8))
            self._rr_row_refs[m.id] = {"match": m, "row": row, "a": lbl_a, "b": lbl_b}

        self.standings_frame = tk.Frame(body, bg=theme.BG)
        self.standings_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

    def _rr_label_click(self, match, team, is_winner):
        if match.winner is None:
            self._record(match, team)
        elif is_winner:
            self._undo(match)

    def _update_rr(self):
        """Refresh every round-robin row's text/color/binding in place and
        rebuild the standings panel (it has no scrollbar, so rebuilding it
        does not lose any scroll position)."""
        for ref in self._rr_row_refs.values():
            m = ref["match"]
            for side, lbl in (("a", ref["a"]), ("b", ref["b"])):
                team = m.team_a if side == "a" else m.team_b
                is_winner = m.winner is team
                is_loser = m.winner is not None and not is_winner
                fg = theme.GOLD if is_winner else theme.TEXT
                font = ("Segoe UI Semibold", 11, "overstrike") if is_loser else ("Segoe UI Semibold", 11)
                clickable = m.winner is None or is_winner
                lbl.configure(text=team.name, fg=fg, font=font,
                               cursor="hand2" if clickable else "arrow")
                lbl.unbind("<Button-1>")
                if clickable:
                    lbl.bind("<Button-1>",
                              lambda e, mm=m, t=team, w=is_winner: self._rr_label_click(mm, t, w))

        for w in self.standings_frame.winfo_children():
            w.destroy()
        tk.Label(self.standings_frame, text="Standings", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))
        for i, (team, wins, played) in enumerate(B.league_standings(self.data)):
            row = tk.Frame(self.standings_frame, bg=theme.PANEL_2)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{i + 1}. {team.name}", fg=theme.TEXT, bg=theme.PANEL_2,
                      font=theme.FONT_BODY, anchor="w").pack(side="left", padx=10, pady=6,
                                                                fill="x", expand=True)
            tk.Label(row, text=f"{wins}-{played - wins}", fg=theme.DIM, bg=theme.PANEL_2,
                      font=theme.FONT_SMALL).pack(side="right", padx=10)

        ready = B.league_round_robin_complete(self.data)
        playoff_btn = tk.Button(self.standings_frame, text="Generate Playoffs", command=self._start_playoffs,
                                  **theme.primary_button_kwargs())
        playoff_btn.pack(fill="x", pady=(14, 0))
        if not ready:
            playoff_btn.configure(state="disabled")

    def _start_playoffs(self):
        B.start_league_playoffs(self.data, playoff_size=min(4, len(self.data.seed_order)))
        self._refresh()

    # ---------- single / double / playoff-stage: canvas tree ----------

    def _grouped_rounds(self, bracket_key):
        by_round = {}
        for m in self.data.matches.values():
            if m.bracket == bracket_key:
                by_round.setdefault(m.round_index, []).append(m)
        return [sorted(by_round[r], key=lambda m: m.id) for r in sorted(by_round)]

    @staticmethod
    def _revealed(m):
        """Only a match a team has actually reached (or already decided)
        is drawn - later rounds appear as results come in, instead of a
        full tree of empty TBD boxes (item 5)."""
        return m.team_a is not None or m.team_b is not None or m.winner is not None

    def _compute_y(self, rounds, box_h, row_gap):
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

    def _render_canvas(self):
        self.canvas.delete("all")
        z = ZOOM_LEVELS[self.zoom_index]
        box_w, box_h = BASE_BOX_W * z, BASE_BOX_H * z
        col_gap, row_gap = BASE_COL_GAP * z, BASE_ROW_GAP * z
        section_gap = SECTION_GAP * z
        section_label_h = SECTION_LABEL_H * z
        round_label_h = ROUND_LABEL_H * z
        font_name = max(8, int(11 * z))
        font_rank = max(7, int(9 * z))
        section_font = ("Segoe UI Semibold", max(9, int(10 * z)))
        round_font = ("Segoe UI", max(8, int(9 * z)))

        max_x, max_y = 0, 0

        def draw_group(rounds, y_offset):
            """y_offset already clears the section title row; this adds its
            own per-column round-name row above the match boxes, so the two
            labels never sit on top of each other."""
            nonlocal max_x, max_y
            matches_top = y_offset + round_label_h
            y = self._compute_y(rounds, box_h, row_gap)
            positions = {}
            for r, round_matches in enumerate(rounds):
                x = r * (box_w + col_gap)
                visible_in_round = [m for m in round_matches if self._revealed(m)]
                if visible_in_round:
                    self.canvas.create_text(x + 4, y_offset + 2, anchor="nw",
                                              text=visible_in_round[0].label or f"Round {r + 1}",
                                              fill=theme.DIM, font=round_font)
                for m in round_matches:
                    if not self._revealed(m):
                        continue
                    top = y[m.id] + matches_top
                    positions[m.id] = (x, top)
                    self._draw_match_box(m, x, top, box_w, box_h, font_name, font_rank)
                    max_x, max_y = max(max_x, x + box_w), max(max_y, top + box_h)
            for round_matches in rounds:
                for m in round_matches:
                    if m.id in positions and m.next_match_id and m.next_match_id in positions:
                        x0, y0 = positions[m.id]
                        x1, y1 = positions[m.next_match_id]
                        self._draw_connector(x0 + box_w, y0 + box_h / 2, x1, y1 + box_h / 2, col_gap)
            bottom = (max((y[m.id] for rm in rounds for m in rm if m.id in positions), default=None))
            bottom = (bottom + matches_top + box_h) if bottom is not None else matches_top
            return positions, bottom

        y_cursor = 0
        w_rounds = self._grouped_rounds("W")
        w_positions = {}
        if w_rounds:
            self.canvas.create_text(4, y_cursor, anchor="nw",
                                      text=("Winners Bracket" if self.data.format == "double" else "Bracket"),
                                      fill=theme.TEXT, font=section_font)
            w_positions, bottom = draw_group(w_rounds, y_cursor + section_label_h)
            y_cursor = bottom + section_gap

        l_rounds = self._grouped_rounds("L")
        l_positions = {}
        if l_rounds and any(self._revealed(m) for rm in l_rounds for m in rm):
            self.canvas.create_text(4, y_cursor, anchor="nw", text="Losers Bracket",
                                      fill=theme.TEXT, font=section_font)
            l_positions, bottom = draw_group(l_rounds, y_cursor + section_label_h)
            y_cursor = bottom + section_gap

        p_rounds = self._grouped_rounds("P")
        if p_rounds:
            self.canvas.create_text(4, y_cursor, anchor="nw", text="Playoffs",
                                      fill=theme.TEXT, font=section_font)
            draw_group(p_rounds, y_cursor + section_label_h)

        gf = self.data.matches.get("GF")
        if gf and self._revealed(gf):
            last_col = max(len(w_rounds), len(l_rounds))
            x = last_col * (box_w + col_gap)
            w_final = w_rounds[-1][0] if w_rounds else None
            l_final = l_rounds[-1][0] if l_rounds else None
            ys = [pos[1] for final, pos in
                  ((w_final, w_positions.get(w_final.id) if w_final else None),
                   (l_final, l_positions.get(l_final.id) if l_final else None)) if pos]
            top = (sum(ys) / len(ys)) if ys else 0
            self.canvas.create_text(x + 4, top - section_label_h + 4, anchor="nw", text="Grand Final",
                                      fill=theme.DIM, font=section_font)
            self._draw_match_box(gf, x, top, box_w, box_h, font_name, font_rank)
            if w_final and w_final.id in w_positions:
                fx, fy = w_positions[w_final.id]
                self._draw_connector(fx + box_w, fy + box_h / 2, x, top + box_h / 2, col_gap)
            if l_final and l_final.id in l_positions:
                fx, fy = l_positions[l_final.id]
                self._draw_connector(fx + box_w, fy + box_h / 2, x, top + box_h / 2, col_gap)
            max_x, max_y = max(max_x, x + box_w), max(max_y, top + box_h)

        self.canvas.configure(scrollregion=(0, 0, max_x + 40, max_y + 40))

    def _draw_match_box(self, m, x, top, box_w, box_h, font_name, font_rank):
        self.canvas.create_rectangle(x, top, x + box_w, top + box_h,
                                        fill=theme.PANEL_2, outline=theme.LINE, width=1)
        half = box_h / 2
        self.canvas.create_line(x, top + half, x + box_w, top + half, fill=theme.LINE)

        for i, (side, team) in enumerate((("a", m.team_a), ("b", m.team_b))):
            ty = top + half * i + half / 2
            if team is None:
                text, fg = ("BYE" if (m.team_a is None) != (m.team_b is None) else "TBD"), theme.DIM
                self.canvas.create_text(x + 10, ty, anchor="w", text=text, fill=fg,
                                          font=("Segoe UI", font_name), width=box_w - 16)
                continue

            is_winner = m.winner is team
            is_loser = m.winner is not None and not is_winner
            fg = theme.GOLD if is_winner else (theme.DIM if is_loser else theme.TEXT)
            item = self.canvas.create_text(x + 10, ty, anchor="w", text=team.name, fill=fg,
                                              font=("Segoe UI Semibold", font_name), width=box_w - 16)
            clickable = False
            if m.winner is None and m.team_a is not None and m.team_b is not None:
                self.canvas.tag_bind(item, "<Button-1>", lambda e, mm=m, t=team: self._record(mm, t))
                clickable = True
            elif is_winner and not m.auto:
                self.canvas.tag_bind(item, "<Button-1>", lambda e, mm=m: self._undo(mm))
                clickable = True
            if clickable:
                self.canvas.tag_bind(item, "<Enter>", lambda e: self.canvas.configure(cursor="hand2"))
                self.canvas.tag_bind(item, "<Leave>", lambda e: self.canvas.configure(cursor="arrow"))

        if m.auto:
            self.canvas.create_text(x + box_w - 6, top + 4, anchor="ne", text="bye",
                                      fill=theme.DIM, font=("Segoe UI", font_rank))

    def _draw_connector(self, x0, y0, x1, y1, col_gap):
        mid = x0 + col_gap / 2
        self.canvas.create_line(x0, y0, mid, y0, fill=theme.LINE)
        self.canvas.create_line(mid, y0, mid, y1, fill=theme.LINE)
        self.canvas.create_line(mid, y1, x1, y1, fill=theme.LINE)
