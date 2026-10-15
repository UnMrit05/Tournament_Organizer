"""Screen 4 - Mystery Hero. Spins a role, then a character, for every player on every team."""

import random
import tkinter as tk

from app.data.roster import characters_for_role
from app.data.save_manager import save_state, serialize_app_state
from app.ui import theme
from app.ui.player_icons import platform_badge, role_badge, role_icons
from app.ui.scrollable import ScrollableFrame
from app.ui.slot_reel import SlotReel


class MysterySpinScreen(tk.Frame):
    """The Mystery Hero page: spin for roles, then characters, one team at a time."""
    def __init__(self, parent, app):
        """Builds the footer, the sorted and upcoming side panes, and the middle spin area."""
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.active_team = None
        self.phase = "role"        # "role" | "character" | "done"
        self.current_pick = None
        self._animating = False
        self._proceed_confirmed = False
        self._pane_boxes = {}      # id(team) -> {"box", "pane", "rows": {ign: {...}}}

        # ---- footer (navigation) pinned to the bottom ----
        footer = tk.Frame(self, bg=theme.BG)
        footer.pack(side="bottom", fill="x", padx=20, pady=16)
        tk.Button(footer, text="Back", command=self._on_previous,
                   **theme.button_kwargs()).pack(side="left", padx=6)
        tk.Button(footer, text="Save", command=self._on_save,
                   **theme.button_kwargs()).pack(side="left", padx=6)
        tk.Button(footer, text="Proceed to Bracket", command=self._on_proceed,
                   **theme.primary_button_kwargs()).pack(side="right", padx=6)
        self.warn_lbl = tk.Label(footer, text="", fg=theme.GOLD, bg=theme.BG, font=theme.FONT_SMALL)
        self.warn_lbl.pack(side="right", padx=12)

        # ---- three columns: sorted teams | spin UI | upcoming teams ----
        # This screen has no top heading, so the body gets a top margin
        # (scaled the same way the toolbar is) to keep the "Upcoming" pane
        # clear of the top-right toolbar at every resolution.
        body = tk.Frame(self, bg=theme.BG)
        body.pack(side="top", fill="both", expand=True, padx=16, pady=(theme.S(34), 0))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.columnconfigure(2, weight=1)
        body.rowconfigure(0, weight=1)

        left_wrap = tk.Frame(body, bg=theme.BG)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(left_wrap, text="Sorted", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))
        self.left_scroll = ScrollableFrame(left_wrap)
        self.left_scroll.pack(fill="both", expand=True)

        center = tk.Frame(body, bg=theme.BG)
        center.grid(row=0, column=1, sticky="nsew")

        right_wrap = tk.Frame(body, bg=theme.BG)
        right_wrap.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        tk.Label(right_wrap, text="Upcoming (click a team to spin for it)", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL, wraplength=theme.S(160), justify="left").pack(anchor="w", pady=(0, 6))
        self.right_scroll = ScrollableFrame(right_wrap)
        self.right_scroll.pack(fill="both", expand=True)

        # ---- the spin UI itself, centered (both axes) within the middle column ----
        wrap = tk.Frame(center, bg=theme.BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        self.phase_lbl = tk.Label(wrap, fg=theme.TEXT, bg=theme.BG, font=theme.font(theme.SEMIBOLD, 24))
        self.phase_lbl.pack()
        self.team_lbl = tk.Label(wrap, fg=theme.DIM, bg=theme.BG, font=theme.FONT_BODY)
        self.team_lbl.pack(pady=(2, 22))

        # -- player info card --
        self.card = tk.Frame(wrap, bg=theme.PANEL, highlightbackground=theme.LINE, highlightthickness=1)
        self.card.pack(pady=(0, 22))
        inner = tk.Frame(self.card, bg=theme.PANEL)
        inner.pack(padx=22, pady=14)
        self.player_progress_lbl = tk.Label(inner, fg=theme.DIM, bg=theme.PANEL, font=theme.FONT_SMALL)
        self.player_progress_lbl.pack(anchor="w")
        self.player_name_lbl = tk.Label(inner, fg=theme.TEXT, bg=theme.PANEL, font=theme.font(theme.SEMIBOLD, 20))
        self.player_name_lbl.pack(anchor="w", pady=(2, 2))
        self.player_team_lbl = tk.Label(inner, fg=theme.GOLD, bg=theme.PANEL, font=theme.FONT_BODY)
        self.player_team_lbl.pack(anchor="w", pady=(0, 4))
        detail_row = tk.Frame(inner, bg=theme.PANEL)
        detail_row.pack(anchor="w")
        self.player_ign_lbl = tk.Label(detail_row, fg=theme.DIM, bg=theme.PANEL, font=theme.FONT_SMALL)
        self.player_ign_lbl.pack(side="left")
        self.player_rank_lbl = tk.Label(detail_row, fg=theme.DIM, bg=theme.PANEL, font=theme.FONT_SMALL)
        self.player_rank_lbl.pack(side="left", padx=(14, 0))
        self.player_platform_frame = tk.Frame(detail_row, bg=theme.PANEL)
        self.player_platform_frame.pack(side="left", padx=(14, 0))
        self.player_roles_frame = tk.Frame(inner, bg=theme.PANEL)
        self.player_roles_frame.pack(anchor="w", pady=(8, 0))

        # -- "all teams sorted" panel, shown instead of the card above once
        # there's nothing left to spin; a fixed size lets its text center
        # both horizontally and vertically within it. --
        self.done_frame = tk.Frame(wrap, bg=theme.PANEL, highlightbackground=theme.LINE,
                                     highlightthickness=1, width=theme.S(300), height=theme.S(150))
        self.done_frame.pack_propagate(False)
        tk.Label(self.done_frame, text="Done", fg=theme.GOLD, bg=theme.PANEL,
                  font=theme.font(theme.SEMIBOLD, 22)).place(relx=0.5, rely=0.5, anchor="center")

        # -- reel --
        self.reel_row = tk.Frame(wrap, bg=theme.BG)
        self.reel_row.pack()
        self.reel = SlotReel(self.reel_row)
        self.reel.pack(side="left")

        self.pool_lbl = tk.Label(wrap, fg=theme.DIM, bg=theme.BG, font=theme.FONT_SMALL)
        self.pool_lbl.pack(pady=(16, 22))

        spin_btns = tk.Frame(wrap, bg=theme.BG)
        spin_btns.pack()
        self.spin_btn = tk.Button(spin_btns, text="Spin", command=self._on_spin_click,
                                    **theme.primary_button_kwargs())
        self.spin_btn.pack(side="left", padx=6)
        self.confirm_btn = tk.Button(spin_btns, text="Confirm", command=self._confirm,
                                       **theme.button_kwargs())
        self.confirm_btn.pack(side="left", padx=6)

        self._activate_team(self._pick_default_team(), reset_previous=False)
        self._refresh_meta()
        self._refresh_side_panes()

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
        """Switches to the clicked team (unless it's already active or finished) and refreshes."""
        if team is self.active_team or self._team_fully_spun(team):
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

    def _on_spin_click(self):
        """Picks a random result and starts the reel spinning towards it."""
        if self._animating or self.phase == "done":
            return
        options = self._current_options()
        if not options:
            self.current_pick = None
            self.reel.set_static("No options left")
            return
        self.current_pick = random.choice(options)
        self._animating = True
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

        # Only the player-detail panel and the two side-pane boxes touched
        # by this confirm change - nothing else is rebuilt, so the screen
        # doesn't blink on every click.
        self._refresh_meta()
        self._refresh_side_panes()

    def _set_controls_enabled(self, spin=True, confirm=True):
        """Turns the Spin and Confirm buttons on or off."""
        self.spin_btn.configure(state="normal" if spin else "disabled")
        self.confirm_btn.configure(state="normal" if confirm else "disabled")

    # ---------- rendering: center spin UI ----------

    def _refresh_meta(self):
        """Updates the middle area: headings, player card, pool text and the reel prompt."""
        team = self.active_team
        player = self._current_player()

        if self.phase == "done" or team is None:
            self.phase_lbl.configure(text="All teams complete")
            self.team_lbl.configure(text="Every player has a role and a character assigned.")
            self.card.pack_forget()
            self.done_frame.pack(pady=(0, 22), before=self.reel_row)
            self.pool_lbl.configure(text="")
            self.reel.set_static("")
            self._set_controls_enabled(spin=False, confirm=False)
            return

        self.done_frame.pack_forget()
        if not self.card.winfo_ismapped():
            self.card.pack(pady=(0, 22), before=self.reel_row)

        order = self._spin_order(team)
        idx = order.index(player) + 1
        phase_label = "Role Spin" if self.phase == "role" else "Character Spin"
        self.phase_lbl.configure(text=phase_label)
        self.team_lbl.configure(text=team.name)

        self.player_progress_lbl.configure(text=f"Player {idx} of {len(order)}")
        self.player_name_lbl.configure(text=player.twitch)
        self.player_team_lbl.configure(text=f"{team.name}  ·  Captain: {team.captain.twitch}")
        self.player_ign_lbl.configure(text=f"In-game: {player.ign}")
        self.player_rank_lbl.configure(text=f"Peak: {player.peak_rank}")
        for w in self.player_platform_frame.winfo_children():
            w.destroy()
        badge = platform_badge(self.player_platform_frame, player.platform, theme.PANEL, size=20)
        if badge is not None:
            badge.pack(side="left")
            tk.Label(self.player_platform_frame, text=player.platform, fg=theme.DIM, bg=theme.PANEL,
                      font=theme.FONT_SMALL).pack(side="left", padx=(4, 0))

        for w in self.player_roles_frame.winfo_children():
            w.destroy()
        tk.Label(self.player_roles_frame, text="Prefers:", fg=theme.DIM, bg=theme.PANEL,
                  font=theme.FONT_SMALL).pack(side="left", padx=(0, 6))
        for role in player.preferred_roles:
            badge = role_badge(self.player_roles_frame, role, theme.PANEL, size=15)
            if badge is not None:
                badge.pack(side="left", padx=4)
            tk.Label(self.player_roles_frame, text=role, fg=theme.ROLE_COLOR.get(role, theme.DIM),
                      bg=theme.PANEL, font=theme.FONT_SMALL).pack(side="left")

        if self.phase == "role":
            self.pool_lbl.configure(
                text="   ".join(f"{r} ×{c}" for r, c in team.role_pool.items()))
        else:
            role = team.player_roles.get(player.ign, "")
            remaining = len(self._character_options(team, role))
            self.pool_lbl.configure(text=f"{remaining} {role} character(s) available")

        self.reel.set_static("Press Spin")
        self._set_controls_enabled(spin=True, confirm=False)

    # ---------- rendering: side panes ----------

    def _refresh_side_panes(self):
        """Updates the team boxes in the side panes, only rebuilding one when its team switches panes."""
        for team in self.app.teams:
            done = self._team_fully_spun(team)
            pane = "left" if done else "right"
            key = id(team)
            info = self._pane_boxes.get(key)
            if info is None or info["pane"] != pane:
                if info is not None:
                    info["box"].destroy()
                target = self.left_scroll.body if pane == "left" else self.right_scroll.body
                info = self._build_pane_team_box(target, team, pane)
                self._pane_boxes[key] = info
            else:
                self._update_pane_team_box(info, team, pane)

    def _fill_role_icons(self, frame, team, p):
        """Refills one player's little icon row: their spun role if they have one, else their preferred roles."""
        for w in frame.winfo_children():
            w.destroy()
        role = team.player_roles.get(p.ign)
        if role:
            badge = role_badge(frame, role, theme.PANEL, size=12)
            if badge is not None:
                badge.pack(side="left")
        else:
            role_icons(frame, p, theme.PANEL, size=11).pack(side="left")

    def _build_pane_team_box(self, parent, team, pane):
        """Builds one team's box for the side pane, with a row per player."""
        active = pane == "right" and team is self.active_team
        box = tk.Frame(parent, bg=theme.PANEL,
                         highlightbackground=theme.GOLD if active else theme.LINE,
                         highlightthickness=theme.S(2) if active else 1)
        box.pack(fill="x", pady=(0, 6))
        if pane == "right":
            for w in (box,):
                w.bind("<Button-1>", lambda e, t=team: self._select_team(t))
            box.configure(cursor="hand2")

        name_lbl = tk.Label(box, text=team.name, fg=theme.GOLD, bg=theme.PANEL,
                              font=theme.font(theme.SEMIBOLD, 9))
        name_lbl.pack(anchor="w", padx=7, pady=(6, 3))

        rows = {}
        for p in self._spin_order(team):
            row = tk.Frame(box, bg=theme.PANEL)
            row.pack(fill="x", padx=7, pady=1)
            name_fg = theme.GOLD if p is team.captain else theme.TEXT
            player_lbl = tk.Label(row, text=p.twitch, fg=name_fg, bg=theme.PANEL,
                                    font=theme.font(theme.SANS, 7.5))
            player_lbl.pack(side="left")
            # Packed right-to-left: character (rightmost) first, then the
            # role icon(s) just to its left - so icons sit to the RIGHT of
            # the name, never under/behind it.
            char_lbl = tk.Label(row, text=team.player_characters.get(p.ign, ""),
                                  fg=theme.DIM, bg=theme.PANEL, font=theme.font(theme.SANS, 7.5), anchor="e")
            char_lbl.pack(side="right")
            roles_frame = tk.Frame(row, bg=theme.PANEL)
            roles_frame.pack(side="right", padx=(0, 6))
            self._fill_role_icons(roles_frame, team, p)
            if pane == "right":
                for w in (row, player_lbl, roles_frame, char_lbl):
                    w.bind("<Button-1>", lambda e, t=team: self._select_team(t))
            rows[p.ign] = {"roles_frame": roles_frame, "char_lbl": char_lbl}

        tk.Frame(box, bg=theme.PANEL, height=theme.S(3)).pack(fill="x")
        return {"box": box, "pane": pane, "rows": rows}

    def _update_pane_team_box(self, info, team, pane):
        """Updates an existing team box in place (highlight, icons and characters)."""
        active = pane == "right" and team is self.active_team
        info["box"].configure(highlightbackground=theme.GOLD if active else theme.LINE,
                                highlightthickness=theme.S(2) if active else 1)
        for p in self._spin_order(team):
            row_widgets = info["rows"].get(p.ign)
            if not row_widgets:
                continue
            self._fill_role_icons(row_widgets["roles_frame"], team, p)
            row_widgets["char_lbl"].configure(text=team.player_characters.get(p.ign, ""))

    # ---------- footer actions ----------

    def _on_previous(self):
        """Back button: wipes all spins and goes back to Tournament Type."""
        # Back goes to Tournament Type and wipes every team's spin progress,
        # since re-picking Mystery Hero from there starts the spins over.
        for t in self.app.teams:
            t.reset_mystery()
        self.app.show_screen("tournament_type")

    def _on_save(self):
        """Saves the tournament as it is right now."""
        save_state(serialize_app_state(self.app), status="Spin")
        self.warn_lbl.configure(text="Saved.")

    def _on_proceed(self):
        """Goes on to Bracket Settings, warning once first if anyone isn't confirmed."""
        incomplete = [t for t in self.app.teams
                       if len(t.player_characters) < len(self._spin_order(t))]
        if incomplete and not self._proceed_confirmed:
            self.warn_lbl.configure(text="Not everyone is confirmed. Click Proceed again to continue anyway.")
            self._proceed_confirmed = True
            return
        self._proceed_confirmed = False
        # Remember we came from Mystery Hero, so Bracket Settings' Back
        # button returns here instead of to Tournament Type.
        self.app.bracket_settings_origin = "mystery_spin"
        self.app.show_screen("bracket_settings")
