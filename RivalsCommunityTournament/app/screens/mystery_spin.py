"""Screen 4 — Mystery Hero: role & character spin.

Processes one team at a time: spins/confirms a role for every player
(captain included) against that team's 2/2/2 role pool, then spins/
confirms a character for every player - restricted to their confirmed
role and unique within the team - before moving to the next team.
Role and character pools are independent per team.

v0.23: the spin no longer starts automatically - the user clicks
Spin. Layout is centered on the screen; the phase name ("Role Spin" /
"Character Spin") is the heading with the team name as a subheading;
during the character phase the assigned role's icon flanks both sides
of the reel; the player info panel is larger and shows more detail.

v0.30: the spin UI now sits between two side panes - left lists teams
whose roles and characters are both fully spun (role icon + assigned
character per player), right lists teams still waiting their turn
(preferred-role icons only, since nothing's assigned yet), each team
boxed off the same way Drafting's team list is.
"""

import random
import tkinter as tk

from app.data.icons import get_role_glyph
from app.data.roster import characters_for_role
from app.data.save_manager import save_state, serialize_app_state
from app.ui import theme
from app.ui.player_icons import platform_badge, role_icons
from app.ui.scrollable import ScrollableFrame
from app.ui.slot_reel import SlotReel


class MysterySpinScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.team_index = 0
        self.phase = "role"        # "role" | "character" | "done"
        self.current_pick = None
        self._animating = False
        self._proceed_confirmed = False

        # ---- footer (navigation) pinned to the bottom ----
        footer = tk.Frame(self, bg=theme.BG)
        footer.pack(side="bottom", fill="x", padx=20, pady=16)
        tk.Button(footer, text="Previous", command=self._on_previous,
                   **theme.button_kwargs()).pack(side="left", padx=6)
        tk.Button(footer, text="Save", command=self._on_save,
                   **theme.button_kwargs()).pack(side="left", padx=6)
        tk.Button(footer, text="Proceed to Bracket", command=self._on_proceed,
                   **theme.primary_button_kwargs()).pack(side="right", padx=6)
        self.warn_lbl = tk.Label(footer, text="", fg=theme.GOLD, bg=theme.BG, font=theme.FONT_SMALL)
        self.warn_lbl.pack(side="right", padx=12)

        # ---- three columns: already-spun teams | spin UI | upcoming teams ----
        body = tk.Frame(self, bg=theme.BG)
        body.pack(side="top", fill="both", expand=True, padx=16, pady=(6, 0))
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.columnconfigure(2, weight=2)
        body.rowconfigure(0, weight=1)

        left_wrap = tk.Frame(body, bg=theme.BG)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(left_wrap, text="Already spun", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))
        self.left_scroll = ScrollableFrame(left_wrap)
        self.left_scroll.pack(fill="both", expand=True)

        center = tk.Frame(body, bg=theme.BG)
        center.grid(row=0, column=1, sticky="nsew")

        right_wrap = tk.Frame(body, bg=theme.BG)
        right_wrap.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        tk.Label(right_wrap, text="Upcoming", fg=theme.DIM, bg=theme.BG,
                  font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 6))
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
        card = tk.Frame(wrap, bg=theme.PANEL, highlightbackground=theme.LINE, highlightthickness=1)
        card.pack(pady=(0, 22))
        inner = tk.Frame(card, bg=theme.PANEL)
        inner.pack(padx=22, pady=14)
        self.player_progress_lbl = tk.Label(inner, fg=theme.DIM, bg=theme.PANEL, font=theme.FONT_SMALL)
        self.player_progress_lbl.pack(anchor="w")
        self.player_name_lbl = tk.Label(inner, fg=theme.TEXT, bg=theme.PANEL, font=theme.font(theme.SEMIBOLD, 20))
        self.player_name_lbl.pack(anchor="w", pady=(2, 2))
        self.player_team_lbl = tk.Label(inner, fg=theme.GOLD, bg=theme.PANEL, font=theme.FONT_BODY)
        self.player_team_lbl.pack(anchor="w", pady=(0, 4))
        detail_row = tk.Frame(inner, bg=theme.PANEL)
        detail_row.pack(anchor="w")
        self.player_twitch_lbl = tk.Label(detail_row, fg=theme.DIM, bg=theme.PANEL, font=theme.FONT_SMALL)
        self.player_twitch_lbl.pack(side="left")
        self.player_rank_lbl = tk.Label(detail_row, fg=theme.DIM, bg=theme.PANEL, font=theme.FONT_SMALL)
        self.player_rank_lbl.pack(side="left", padx=(14, 0))
        self.player_platform_frame = tk.Frame(detail_row, bg=theme.PANEL)
        self.player_platform_frame.pack(side="left", padx=(14, 0))
        self.player_roles_frame = tk.Frame(inner, bg=theme.PANEL)
        self.player_roles_frame.pack(anchor="w", pady=(8, 0))

        # -- reel, flanked by role icons during the character phase --
        reel_row = tk.Frame(wrap, bg=theme.BG)
        reel_row.pack()
        self.flank_left = tk.Label(reel_row, text="", fg=theme.DIM, bg=theme.BG,
                                     font=theme.font(theme.SANS, 22), width=3)
        self.flank_left.pack(side="left", padx=(0, 14))
        self.reel = SlotReel(reel_row)
        self.reel.pack(side="left")
        self.flank_right = tk.Label(reel_row, text="", fg=theme.DIM, bg=theme.BG,
                                      font=theme.font(theme.SANS, 22), width=3)
        self.flank_right.pack(side="left", padx=(14, 0))

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

        self._advance_to_next_pending()
        self._refresh_meta()
        self._refresh_side_panes()

    # ---------- sequencing ----------

    def _current_team(self):
        if self.team_index >= len(self.app.teams):
            return None
        return self.app.teams[self.team_index]

    def _spin_order(self, team):
        return [team.captain] + [p for p in team.slots if p is not None]

    def _first_unresolved(self, team, phase):
        target = team.player_roles if phase == "role" else team.player_characters
        for p in self._spin_order(team):
            if p.ign not in target:
                return p
        return None

    def _current_player(self):
        team = self._current_team()
        if team is None or self.phase == "done":
            return None
        return self._first_unresolved(team, self.phase)

    def _advance_to_next_pending(self):
        while self.team_index < len(self.app.teams):
            team = self._current_team()
            if self._first_unresolved(team, "role") is not None:
                self.phase = "role"
                return
            if self._first_unresolved(team, "character") is not None:
                self.phase = "character"
                return
            self.team_index += 1
        self.phase = "done"

    # ---------- spinning ----------

    def _weighted_role_options(self, team):
        return [r for r, cnt in team.role_pool.items() for _ in range(cnt)]

    def _character_options(self, team, role):
        if not role:
            return []
        used = set(team.player_characters.values())
        return [c.name for c in characters_for_role(self.app.roster, role) if c.name not in used]

    def _current_options(self):
        team = self._current_team()
        if team is None or self.phase == "done":
            return []
        if self.phase == "role":
            return self._weighted_role_options(team)
        player = self._current_player()
        role = team.player_roles.get(player.ign) if player else None
        return self._character_options(team, role)

    def _on_spin_click(self):
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
        self._animating = False
        self._set_controls_enabled(spin=True, confirm=True)

    def _confirm(self):
        if self._animating:
            return
        team = self._current_team()
        player = self._current_player()
        if not team or not player or self.current_pick is None:
            return
        if self.phase == "role":
            team.player_roles[player.ign] = self.current_pick
            team.role_pool[self.current_pick] -= 1
        else:
            team.player_characters[player.ign] = self.current_pick
        self.current_pick = None
        self._advance_to_next_pending()
        self._refresh_meta()
        self._refresh_side_panes()

    def _set_controls_enabled(self, spin=True, confirm=True):
        self.spin_btn.configure(state="normal" if spin else "disabled")
        self.confirm_btn.configure(state="normal" if confirm else "disabled")

    # ---------- rendering: center spin UI ----------

    def _refresh_meta(self):
        team = self._current_team()
        player = self._current_player()

        if self.phase == "done" or team is None:
            self.phase_lbl.configure(text="All teams complete")
            self.team_lbl.configure(text="Every player has a role and a character assigned.")
            self.player_progress_lbl.configure(text="")
            self.player_name_lbl.configure(text="✓ Done")
            self.player_team_lbl.configure(text="")
            for w in self.player_platform_frame.winfo_children():
                w.destroy()
            self.player_twitch_lbl.configure(text="")
            self.player_rank_lbl.configure(text="")
            for w in self.player_roles_frame.winfo_children():
                w.destroy()
            self.flank_left.configure(text="")
            self.flank_right.configure(text="")
            self.pool_lbl.configure(text="")
            self.reel.set_static("✓")
            self._set_controls_enabled(spin=False, confirm=False)
            return

        order = self._spin_order(team)
        idx = order.index(player) + 1
        phase_label = "Role Spin" if self.phase == "role" else "Character Spin"
        self.phase_lbl.configure(text=phase_label)
        self.team_lbl.configure(text=team.name)

        self.player_progress_lbl.configure(text=f"Player {idx} of {len(order)}")
        self.player_name_lbl.configure(text=player.ign)
        self.player_team_lbl.configure(text=f"{team.name}  ·  Captain: {team.captain.ign}")
        self.player_twitch_lbl.configure(
            text=f"twitch.tv/{player.twitch}" if player.twitch else "No Twitch linked")
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
            tk.Label(self.player_roles_frame, text=f"{get_role_glyph(role)} {role}",
                      fg=theme.ROLE_COLOR.get(role, theme.DIM), bg=theme.PANEL,
                      font=theme.FONT_SMALL).pack(side="left", padx=4)

        if self.phase == "character":
            role = team.player_roles.get(player.ign, "")
            glyph = get_role_glyph(role)
            color = theme.ROLE_COLOR.get(role, theme.DIM)
            self.flank_left.configure(text=glyph, fg=color)
            self.flank_right.configure(text=glyph, fg=color)
        else:
            self.flank_left.configure(text="")
            self.flank_right.configure(text="")

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

    def _team_fully_spun(self, team):
        order = self._spin_order(team)
        return all(p.ign in team.player_characters for p in order)

    def _refresh_side_panes(self):
        """Rebuilt in full on every spin/confirm - there are only ever a
        handful of teams, so this is cheap, unlike the larger lists
        elsewhere in the app that update in place to protect scroll
        position."""
        for w in self.left_scroll.body.winfo_children():
            w.destroy()
        for w in self.right_scroll.body.winfo_children():
            w.destroy()

        for team in self.app.teams:
            done = self._team_fully_spun(team)
            target = self.left_scroll.body if done else self.right_scroll.body
            self._build_pane_team_box(target, team, done)

    def _build_pane_team_box(self, parent, team, done):
        box = tk.Frame(parent, bg=theme.PANEL, highlightbackground=theme.LINE, highlightthickness=1)
        box.pack(fill="x", pady=(0, 10))
        tk.Label(box, text=team.name, fg=theme.GOLD, bg=theme.PANEL,
                  font=theme.FONT_NAME).pack(anchor="w", padx=10, pady=(8, 4))

        for p in self._spin_order(team):
            row = tk.Frame(box, bg=theme.PANEL)
            row.pack(fill="x", padx=10, pady=2)
            role = team.player_roles.get(p.ign)
            if role:
                tk.Label(row, text=get_role_glyph(role), fg=theme.ROLE_COLOR.get(role, theme.DIM),
                          bg=theme.PANEL, font=theme.FONT_BODY, width=2).pack(side="left")
            else:
                role_icons(row, p, theme.PANEL).pack(side="left")
            name_fg = theme.GOLD if p is team.captain else theme.TEXT
            tk.Label(row, text=p.ign, fg=name_fg, bg=theme.PANEL,
                      font=theme.FONT_SMALL).pack(side="left", padx=(6, 0))
            char = team.player_characters.get(p.ign)
            if char:
                tk.Label(row, text=char, fg=theme.DIM, bg=theme.PANEL,
                          font=theme.FONT_SMALL, anchor="e").pack(side="right")

        tk.Frame(box, bg=theme.PANEL, height=theme.S(4)).pack(fill="x")

    # ---------- footer actions ----------

    def _on_previous(self):
        for t in self.app.teams:
            t.reset_mystery()
        self.app.show_screen("seeding")

    def _on_save(self):
        save_state(serialize_app_state(self.app), status="Spin")
        self.warn_lbl.configure(text="Saved.")

    def _on_proceed(self):
        incomplete = [t for t in self.app.teams
                       if len(t.player_characters) < len(self._spin_order(t))]
        if incomplete and not self._proceed_confirmed:
            self.warn_lbl.configure(text="Not everyone is confirmed. Click Proceed again to continue anyway.")
            self._proceed_confirmed = True
            return
        self._proceed_confirmed = False
        self.app.show_screen("bracket_settings")
