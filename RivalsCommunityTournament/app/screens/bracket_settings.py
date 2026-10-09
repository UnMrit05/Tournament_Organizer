"""Screen 5 — Bracket Settings.

Seed order is a drag-and-drop list: grab a row (the \u2261 handle or anywhere
on its text) and drag it up or down; the ▲/▼ buttons do the same one step
at a time. Rows are built once and only their contents are updated, so
reordering or switching format never rebuilds the screen.

Buttons: Confirm builds the bracket and opens the Bracket screen,
Previous returns to the Mystery Hero screen, Save writes the save file
with state "Bracket Setting" (restored by Continue on the Greeting screen).
"""

import tkinter as tk

from app.data import bracket as B
from app.data.save_manager import save_state, serialize_app_state
from app.ui import theme
from app.ui.scrollable import ScrollableFrame

FORMATS = [
    ("single", "Single Elimination"),
    ("double", "Double Elimination"),
    ("league", "League + Playoffs"),
]


class BracketSettingsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app

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
        self._row_refs = []
        self.format_buttons = {}

        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill="x", padx=20, pady=(16, 6))
        tk.Label(header, text="Bracket Settings", fg=theme.TEXT, bg=theme.BG,
                  font=theme.FONT_HEADING).pack(side="left")

        # Footer first so it always keeps its space at the bottom.
        footer = tk.Frame(self, bg=theme.BG)
        footer.pack(side="bottom", fill="x", padx=20, pady=14)
        self.status_lbl = tk.Label(footer, text="", fg=theme.GOLD, bg=theme.BG, font=theme.FONT_SMALL)
        self.status_lbl.pack(side="left", padx=12)
        self.confirm_btn = tk.Button(footer, text="Confirm", command=self._on_confirm,
                                       **theme.primary_button_kwargs())
        self.confirm_btn.pack(side="right")
        tk.Button(footer, text="Save", command=self._on_save,
                   **theme.button_kwargs()).pack(side="right", padx=8)
        tk.Button(footer, text="Previous", command=lambda: app.show_screen("mystery_spin"),
                   **theme.button_kwargs()).pack(side="right")
        if len(self.order) < 2:
            self.confirm_btn.configure(state="disabled")
            self.status_lbl.configure(text="Need at least 2 teams to start.")

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True, padx=20, pady=6)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=theme.BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(left, text="Seed order \u2014 drag to reorder (top = seed 1)", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))
        self.order_scroll = ScrollableFrame(left)
        self.order_scroll.pack(fill="both", expand=True)

        right = tk.Frame(body, bg=theme.BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        tk.Label(right, text="Bracket type", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))
        self.format_frame = tk.Frame(right, bg=theme.BG)
        self.format_frame.pack(anchor="w", fill="x")
        self._build_format_options()

        self.hint_lbl = tk.Label(right, fg=theme.DIM, bg=theme.BG, font=theme.FONT_SMALL,
                                   wraplength=320, justify="left")
        self.hint_lbl.pack(anchor="w", pady=(16, 0))
        self._update_hint()

        self._build_order_rows()

    # ---------- format selector (recolors buttons in place) ----------

    def _build_format_options(self):
        for key, label in FORMATS:
            btn = tk.Button(self.format_frame, text=label, anchor="w",
                              command=lambda k=key: self._pick_format(k), **theme.button_kwargs())
            btn.pack(fill="x", pady=4)
            self.format_buttons[key] = btn
        self._restyle_format_buttons()

    def _pick_format(self, key):
        self.selected_format = key
        self.app.bracket_type = key
        self._restyle_format_buttons()
        self._update_hint()

    def _restyle_format_buttons(self):
        for key, btn in self.format_buttons.items():
            selected = key == self.selected_format
            btn.configure(bg=theme.GOLD if selected else theme.PANEL_2,
                           fg="#181205" if selected else theme.TEXT,
                           activebackground=theme.GOLD if selected else theme.LINE)

    def _update_hint(self):
        n = len(self.order)
        size = B.next_power_of_two(max(n, 2))
        byes = f"{size - n} bye{'s' if size - n != 1 else ''}"
        hints = {
            "single": f"{n} teams, bracket size {size} ({byes}). One loss eliminates a team.",
            "double": f"{n} teams, bracket size {size} ({byes}). A team is eliminated on their second loss.",
            "league": f"{n} teams play a full round robin ({n * (n - 1) // 2} matches), then the "
                       f"top {min(4, n)} advance to a single-elimination playoff.",
        }
        self.hint_lbl.configure(text=hints.get(self.selected_format, ""))

    # ---------- seed order: rows are built ONCE, pinned to positions ----------

    def _build_order_rows(self):
        for i in range(len(self.order)):
            row = tk.Frame(self.order_scroll.body, bg=theme.PANEL_2,
                             highlightbackground=theme.LINE, highlightthickness=1)
            row.pack(fill="x", pady=3)

            grip = tk.Label(row, text="\u2261", fg=theme.DIM, bg=theme.PANEL_2,
                              font=theme.font(theme.SANS, 16), cursor="fleur", padx=8)
            grip.pack(side="left")
            num = tk.Label(row, fg=theme.GOLD, bg=theme.PANEL_2,
                             font=theme.font(theme.SEMIBOLD, 11), width=3, cursor="fleur")
            num.pack(side="left", padx=(0, 4), pady=8)
            info = tk.Frame(row, bg=theme.PANEL_2, cursor="fleur")
            info.pack(side="left", fill="x", expand=True, pady=8)
            name = tk.Label(info, fg=theme.TEXT, bg=theme.PANEL_2,
                              font=theme.font(theme.SEMIBOLD, 11), cursor="fleur")
            name.pack(anchor="w")
            cap = tk.Label(info, fg=theme.DIM, bg=theme.PANEL_2, font=theme.FONT_SMALL, cursor="fleur")
            cap.pack(anchor="w")

            btns = tk.Frame(row, bg=theme.PANEL_2)
            btns.pack(side="right", padx=8)
            up = tk.Button(btns, text="\u25b2", command=lambda idx=i: self._move(idx, -1),
                             **theme.button_kwargs())
            up.configure(padx=8, pady=2)
            up.pack(side="left", padx=2)
            down = tk.Button(btns, text="\u25bc", command=lambda idx=i: self._move(idx, 1),
                               **theme.button_kwargs())
            down.configure(padx=8, pady=2)
            down.pack(side="left", padx=2)

            for w in (row, grip, num, info, name, cap):
                w.bind("<ButtonPress-1>", lambda e, idx=i: self._drag_start(idx))
                w.bind("<B1-Motion>", self._drag_motion)
                w.bind("<ButtonRelease-1>", self._drag_end)

            self._row_refs.append({"row": row, "grip": grip, "num": num, "info": info, "name": name,
                                     "cap": cap, "btns": btns, "up": up, "down": down})
            self._update_order_row(i)

    def _update_order_row(self, i):
        """Refresh one row's contents/colors in place - no widgets are rebuilt."""
        ref = self._row_refs[i]
        team = self.order[i]
        bg = theme.ACTIVE_BG if self._drag_index == i else theme.PANEL_2
        ref["num"].configure(text=str(i + 1))
        ref["name"].configure(text=team.name)
        ref["cap"].configure(text=f"Captain: {team.captain.ign}")
        for key in ("row", "grip", "num", "info", "name", "cap", "btns"):
            ref[key].configure(bg=bg)
        ref["row"].configure(highlightbackground=theme.GOLD if self._drag_index == i else theme.LINE)
        ref["up"].configure(state="disabled" if i == 0 else "normal")
        ref["down"].configure(state="disabled" if i == len(self.order) - 1 else "normal")

    def _move(self, index, delta):
        j = index + delta
        if 0 <= j < len(self.order):
            B.move_item(self.order, index, j)
            self._update_order_row(index)
            self._update_order_row(j)

    # ---------- drag and drop ----------

    def _drag_start(self, index):
        self._drag_index = index
        self._update_order_row(index)

    def _index_at(self, rel_y):
        """Which (fixed) row band the pointer is over, clamped to the list."""
        for i, ref in enumerate(self._row_refs):
            top = ref["row"].winfo_y()
            if top <= rel_y < top + ref["row"].winfo_height():
                return i
        first = self._row_refs[0]["row"].winfo_y()
        return 0 if rel_y < first else len(self._row_refs) - 1

    def _drag_motion(self, event):
        if self._drag_index is None or not self._row_refs:
            return
        rel_y = event.y_root - self.order_scroll.body.winfo_rooty()
        target = self._index_at(rel_y)
        old = self._drag_index
        if target != old:
            B.move_item(self.order, old, target)
            self._drag_index = target
            for i in range(min(old, target), max(old, target) + 1):
                self._update_order_row(i)

    def _drag_end(self, event):
        index = self._drag_index
        self._drag_index = None
        if index is not None:
            self._update_order_row(index)

    # ---------- footer actions ----------

    def _on_confirm(self):
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
        save_state(serialize_app_state(self.app), status="Bracket Setting")
        self.status_lbl.configure(text="Saved. Use Continue on the start screen to resume here.")
