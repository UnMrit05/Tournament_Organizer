"""The drafting screen: pick players for each team's open slots from the pool on the right."""

import tkinter as tk
from tkinter import ttk

from app.data.ranks import RANK_TIERS, matches_tier, strip_subdivision
from app.data.save_manager import save_state, serialize_app_state
from app.data.team import next_open_slot
from app.ui import theme
from app.ui.player_icons import name_with_platform, role_icons
from app.ui.scrollable import ScrollableFrame

TIER_OPTIONS = ["Any"] + RANK_TIERS


class SeedingScreen(tk.Frame):
    """Drafting screen with the teams on the left and the undrafted players on the right."""
    def __init__(self, parent, app):
        """Sets up the whole screen: team panels, roster list, search box and the bottom buttons."""
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.active = None            # (team_index, slot_index) or None
        self._lock_confirmed = False
        self._slot_refs = {}          # (ti, si) -> widget refs
        self._roster_refs = []        # one entry per pool row
        self._name_vars = []          # (team, StringVar) - committed explicitly on Save/Lock Seed

        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill="x", padx=20, pady=(16, 6))
        tk.Label(header, text="Drafting", fg=theme.TEXT, bg=theme.BG,
                  font=theme.FONT_HEADING).pack(side="left")

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True, padx=20, pady=6)
        body.columnconfigure(0, weight=6)
        body.columnconfigure(1, weight=5)
        body.rowconfigure(0, weight=1)

        left_wrap = tk.Frame(body, bg=theme.BG)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(left_wrap, text="Teams", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))
        self.left_scroll = ScrollableFrame(left_wrap)
        self.left_scroll.pack(fill="both", expand=True)

        right_wrap = tk.Frame(body, bg=theme.BG)
        right_wrap.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        tk.Label(right_wrap, text="Player roster (highest rank first)", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))

        search_row = tk.Frame(right_wrap, bg=theme.BG)
        search_row.pack(fill="x", pady=(0, 6))
        tk.Label(search_row, text="\U0001F50D", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_row, textvariable=self.search_var, bg=theme.PANEL_2,
                                  fg=theme.TEXT, insertbackground=theme.TEXT, relief="flat",
                                  font=theme.FONT_SMALL)
        search_entry.pack(side="left", fill="x", expand=True, ipady=theme.S(3))
        search_entry.bind("<KeyRelease>", lambda e: self._restyle_roster())
        clear_btn = tk.Label(search_row, text="✕", fg=theme.DIM, bg=theme.BG,
                               font=theme.FONT_SMALL, cursor="hand2")
        clear_btn.pack(side="left", padx=(6, 0))
        clear_btn.bind("<Button-1>", lambda e: self._clear_search())

        self.filter_note = tk.Label(right_wrap, text="", fg=theme.DIM, bg=theme.BG,
                                      font=theme.FONT_SMALL, wraplength=360, justify="left")
        self.filter_note.pack(anchor="w", pady=(0, 6))
        self.right_scroll = ScrollableFrame(right_wrap)
        self.right_scroll.pack(fill="both", expand=True)

        # Footer: buttons on the right, Lock Seed farthest right.
        footer = tk.Frame(self, bg=theme.BG)
        footer.pack(fill="x", padx=20, pady=14)
        self.warn_label = tk.Label(footer, text="", fg=theme.GOLD, bg=theme.BG, font=theme.FONT_SMALL)
        self.warn_label.pack(side="left", padx=12)
        tk.Button(footer, text="Lock Seed", command=self._on_lock,
                   **theme.primary_button_kwargs()).pack(side="right")
        tk.Button(footer, text="Save", command=self._on_save,
                   **theme.button_kwargs()).pack(side="right", padx=8)
        tk.Button(footer, text="Reset", command=self._on_reset,
                   **theme.button_kwargs()).pack(side="right")

        self._build_teams_ui()
        self._rebuild_roster()

    # ---------- teams (left column) — built once, updated in place ----------

    def _build_teams_ui(self):
        """Builds one panel per team (captain, team name box, draft slots). Only done once."""
        for ti, team in enumerate(self.app.teams):
            box = tk.Frame(self.left_scroll.body, bg=theme.PANEL,
                             highlightbackground=theme.LINE, highlightthickness=1)
            box.pack(fill="x", pady=(0, 12))

            hd = tk.Frame(box, bg=theme.PANEL_2)
            hd.pack(fill="x")
            tk.Label(hd, text="Captain", fg=theme.GOLD, bg=theme.PANEL_2,
                      font=theme.FONT_SMALL).pack(side="left", padx=10, pady=8)
            name_var = tk.StringVar(value=team.name)
            entry = tk.Entry(hd, textvariable=name_var, bg=theme.PANEL_2, fg=theme.TEXT,
                               insertbackground=theme.TEXT, relief="flat",
                               font=theme.font(theme.SEMIBOLD, 11), justify="right")
            entry.pack(side="right", padx=10, pady=8, fill="x", expand=True)
            entry.bind("<FocusOut>", lambda e, t=team, v=name_var: self._rename(t, v))
            entry.bind("<Return>", lambda e, t=team, v=name_var: self._rename(t, v))
            self._name_vars.append((team, name_var))

            slots_frame = tk.Frame(box, bg=theme.PANEL)
            slots_frame.pack(fill="x", padx=10, pady=8)

            cap_row = tk.Frame(slots_frame, bg=theme.PANEL)
            cap_row.pack(fill="x", pady=3)
            cap_name = name_with_platform(cap_row, team.captain, theme.PANEL,
                                             name_font=theme.FONT_BODY, name_fg=theme.GOLD,
                                             show_roles=True)
            cap_name.pack(side="left")
            tk.Label(cap_row, text=team.captain.peak_rank, fg=theme.DIM, bg=theme.PANEL,
                      font=theme.FONT_SMALL).pack(side="right")

            for si in range(len(team.slots)):
                self._build_slot_row(slots_frame, ti, si)

    def _build_slot_row(self, parent, ti, si):
        """Builds one draft slot row: the player's name, icons and the rank picker."""
        row = tk.Frame(parent, bg=theme.PANEL, cursor="hand2")
        row.pack(fill="x", pady=2)

        name_group = tk.Frame(row, bg=theme.PANEL)
        name_group.pack(side="left", padx=(2, 6), pady=4)
        name_lbl = tk.Label(name_group, fg=theme.DIM, bg=theme.PANEL, font=theme.FONT_BODY, anchor="w")
        name_lbl.pack(side="left")
        # In-game name is a small, fainter tag right next to the Twitch/YT name,
        # since this row is a single compact line with no room for a second row.
        sub_lbl = tk.Label(name_group, fg=theme.DIM, bg=theme.PANEL, font=theme.FONT_SMALL, anchor="w")
        sub_lbl.pack(side="left", padx=(4, 0))
        platform_frame = tk.Frame(name_group, bg=theme.PANEL)
        platform_frame.pack(side="left")

        icons_frame = tk.Frame(row, bg=theme.PANEL)
        icons_frame.pack(side="left", padx=(0, 6))

        rank_var = tk.StringVar(value=self.app.teams[ti].slot_min_rank[si])
        # width 14 fits "Grand Master" and "One Above All" without clipping
        rank_menu = ttk.Combobox(row, textvariable=rank_var, values=TIER_OPTIONS,
                                   state="readonly", width=14, font=theme.FONT_SMALL)
        rank_menu.pack(side="right", pady=4)
        rank_menu.bind("<<ComboboxSelected>>",
                        lambda e, t=ti, s=si, v=rank_var: self._set_min_rank(t, s, v))

        row.bind("<Button-1>", lambda e, t=ti, s=si: self._on_slot_click(t, s))
        name_lbl.bind("<Button-1>", lambda e, t=ti, s=si: self._on_slot_click(t, s))

        self._slot_refs[(ti, si)] = {
            "row": row, "name_group": name_group, "name_lbl": name_lbl, "sub_lbl": sub_lbl,
            "platform_frame": platform_frame, "icons_frame": icons_frame,
            "rank_var": rank_var, "rank_menu": rank_menu,
        }
        self._update_slot(ti, si)

    def _update_slot(self, ti, si):
        """Redraws just this one slot row, without rebuilding anything."""
        ref = self._slot_refs[(ti, si)]
        team = self.app.teams[ti]
        player = team.slots[si]
        row_bg = theme.ACTIVE_BG if self.active == (ti, si) else theme.PANEL

        ref["row"].configure(bg=row_bg)
        ref["name_group"].configure(bg=row_bg)
        ref["name_lbl"].configure(text=(player.twitch if player else "Empty slot"),
                                    fg=(theme.TEXT if player else theme.DIM), bg=row_bg)
        ref["sub_lbl"].configure(text=(f"({player.ign})" if player else ""), bg=row_bg)
        ref["platform_frame"].configure(bg=row_bg)
        ref["icons_frame"].configure(bg=row_bg)
        for w in ref["platform_frame"].winfo_children():
            w.destroy()
        for w in ref["icons_frame"].winfo_children():
            w.destroy()

        if player:
            from app.ui.player_icons import platform_badge
            badge = platform_badge(ref["platform_frame"], player.platform, row_bg, size=18)
            if badge is not None:
                badge.pack(side="left", padx=(4, 0))
            role_icons(ref["icons_frame"], player, row_bg, size=13).pack(side="left")
            # Drafted: lock the selector to the player's tier until undrafted.
            team.slot_min_rank[si] = strip_subdivision(player.peak_rank)
            ref["rank_menu"].configure(state="disabled")
        else:
            ref["rank_menu"].configure(state="readonly")
        ref["rank_var"].set(team.slot_min_rank[si])

    def _rename(self, team, var):
        """Saves the typed team name onto the team (blank names are ignored)."""
        new_name = var.get().strip()
        if new_name:
            team.name = new_name

    def _commit_names(self):
        """Copies every team name box into its team, so a rename is never lost when you hit Save or Lock Seed."""
        for team, var in self._name_vars:
            self._rename(team, var)

    # ---------- interaction handlers ----------

    def _set_active(self, new_active):
        """Marks a slot as the one we're drafting for and refreshes the old and new slot rows."""
        old_active = self.active
        self.active = new_active
        if old_active is not None and old_active != new_active:
            self._update_slot(*old_active)
        if new_active is not None:
            self._update_slot(*new_active)

    def _on_slot_click(self, ti, si):
        """Clicking a filled slot sends the player back to the pool; clicking an empty one selects it (or deselects it)."""
        team = self.app.teams[ti]
        if team.slots[si] is not None:
            # Click on a drafted slot: undraft, return the player to the pool,
            # and unlock the slot's rank selector.
            team.clear_slot(si)
            self._set_active(None)
            self._update_slot(ti, si)
            self._rebuild_roster()  # pool membership changed
            return

        if self.active == (ti, si):
            self._set_active(None)  # click the active empty slot again to deselect
        else:
            self._set_active((ti, si))
        self._restyle_roster()  # filtering changed, pool membership did not

    def _set_min_rank(self, ti, si, var):
        """Runs when you change a slot's rank picker: remembers it and filters the roster to match."""
        self.app.teams[ti].slot_min_rank[si] = var.get()
        self._set_active((ti, si))
        self._restyle_roster()

    def _assign_player(self, player):
        """Puts the clicked player in the active slot, then jumps to the next open slot."""
        ti, si = self.active
        team = self.app.teams[ti]
        team.assign(si, player)          # _update_slot below locks the selector to their tier
        self._update_slot(ti, si)

        target = next_open_slot(self.app.teams, ti, si)
        self._set_active(target)
        if target is not None:
            self.left_scroll.ensure_visible(self._slot_refs[target]["row"])

        self._rebuild_roster()  # pool membership changed

    # ---------- roster (right column) ----------

    def _rebuild_roster(self):
        """Rebuilds the list of undrafted players on the right."""
        for w in self.right_scroll.body.winfo_children():
            w.destroy()
        self._roster_refs = []

        for p in self.app.unassigned_players():
            row = tk.Frame(self.right_scroll.body, bg=theme.PANEL_2, highlightthickness=1)
            row.pack(fill="x", pady=4)

            left = tk.Frame(row, bg=theme.PANEL_2)
            left.pack(side="left", padx=10, pady=8, fill="x", expand=True)
            name_row = name_with_platform(left, p, theme.PANEL_2)
            name_row.pack(anchor="w")
            name_lbl = name_row.winfo_children()[0].winfo_children()[0]
            tk.Label(left, text=p.peak_rank, fg=theme.DIM, bg=theme.PANEL_2,
                      font=theme.FONT_SMALL).pack(anchor="w")

            role_icons(row, p, theme.PANEL_2, size=12).pack(side="right", padx=10)

            self._roster_refs.append({"player": p, "row": row, "name_lbl": name_lbl, "left": left})

        self._restyle_roster()

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
        self.search_var.set("")
        self._restyle_roster()

    def _restyle_roster(self):
        """Hides the roster rows that don't match the rank filter or search, and updates the note above the list."""
        tier = None
        query = self.search_var.get().strip().lower()
        if self.active is None:
            self.filter_note.configure(
                text=f"{len(self._roster_refs)} undrafted. Select a slot on the left to filter and draft.")
        else:
            ti, si = self.active
            chosen = self.app.teams[ti].slot_min_rank[si]
            tier = None if chosen == "Any" else chosen
            req = "any rank" if tier is None else f"{tier} players only"
            self.filter_note.configure(
                text=f"Drafting for {self.app.teams[ti].name} \u2014 slot {si + 1} ({req}).")

        shown = 0
        for ref in self._roster_refs:
            p = ref["player"]
            rank_ok = self.active is None or tier is None or matches_tier(p.peak_rank, tier)
            search_ok = not query or self._fuzzy_match(query, p.ign) or self._fuzzy_match(query, p.twitch)
            visible = rank_ok and search_ok
            if not visible:
                ref["row"].pack_forget()
                continue
            shown += 1
            ref["row"].pack(fill="x", pady=4)     # re-pack in original (rank-sorted) order

            selectable = self.active is not None
            ref["row"].configure(highlightbackground=theme.GOLD if selectable else theme.LINE,
                                    cursor="hand2" if selectable else "arrow")
            ref["name_lbl"].configure(fg=theme.TEXT)

            ref["row"].unbind("<Button-1>")
            ref["left"].unbind("<Button-1>")
            if selectable:
                ref["row"].bind("<Button-1>", lambda e, pl=p: self._assign_player(pl))
                ref["left"].bind("<Button-1>", lambda e, pl=p: self._assign_player(pl))
        if shown == 0 and (self.active is not None or query):
            self.filter_note.configure(text=self.filter_note.cget("text") + "  (no matching players)")

    # ---------- footer actions ----------

    def _on_lock(self):
        """Moves on to the next screen. If some slots are empty, it warns first and needs a second click."""
        self._commit_names()
        incomplete = [t for t in self.app.teams if not t.is_full()]
        if incomplete and not self._lock_confirmed:
            names = ", ".join(t.name for t in incomplete)
            self.warn_label.configure(
                text=f"Not all slots filled ({names}). Click Lock Seed again to proceed anyway.")
            self._lock_confirmed = True
            return
        self._lock_confirmed = False
        self.app.show_screen("tournament_type")

    def _on_reset(self):
        """Empties every slot and puts everybody back in the pool."""
        for ti, team in enumerate(self.app.teams):
            team.slots = [None] * len(team.slots)
            team.slot_min_rank = ["Any"] * len(team.slot_min_rank)
            for si in range(len(team.slots)):
                self._update_slot(ti, si)
        self.active = None
        self._lock_confirmed = False
        self.warn_label.configure(text="")
        self._rebuild_roster()

    def _on_save(self):
        """Saves the current draft to the save file."""
        self._commit_names()
        save_state(serialize_app_state(self.app), status="Seed")
        self.warn_label.configure(text="Draft saved. Use Continue on the start screen to resume.")
