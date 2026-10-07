# Changelog

## v0.27
**Simplification pass**
- Removed the background-image/blur/"glass" system entirely (`app/ui/background.py`,
  `app/ui/glass.py`, the per-screen `attach()` call, and the app-level backdrop and glass-edge
  margin in `app_state.py`). Every screen is now a plain black background
  (`theme.BG`) — no image, no blur, no dimming, no inset border. `assets/background.png` is no
  longer read by the app (the file itself is left in place in case you want it back later).
- Reverted the Mystery Hero screen to its v0.25 behavior: the v0.26 pull-lever (`app/ui/lever.py`,
  now removed) is gone, and the Spin/Respin button is back. This also fixes the screen rendering
  fully black in v0.26.

## v0.26
**Scaling & window**
- The UI now scales to the screen height (1440p and other high resolutions get noticeably larger
  text/controls instead of a tiny fixed layout), via `theme.S()`/`theme.font()` and
  `theme.init_scale()`; a manual override is still available via `Scale:` in
  `assets/tournament_info.txt`.
- The window now opens maximized ("zoomed") to fill the screen by default.
- Added a persistent fullscreen toggle button in the top-right corner (survives every screen
  change) plus Escape to exit fullscreen.

**Drafting**
- Platform icon now sits directly next to the player's name (captain rows, slots, roster) instead
  of being grouped with the preferred-role icons.
- Rank filtering now **hides** non-matching players entirely instead of just greying them out, so
  the roster only ever shows players at the selected rank.

**Mystery Hero**
- Replaced the Spin/Respin buttons with an interactive pull-lever next to the slot reel — click
  and drag (or just click) the lever's handle to spin; Confirm is unchanged.

**Bracket**
- The bracket now only draws a team's actual starting position up front; a later round's match box
  only appears once a team has actually arrived there, instead of a full tree of empty "TBD" boxes.
- Fixed the "Round 1" / "Losers Bracket" (and other section/round) labels overlapping the bracket
  itself — the section title, the per-column round name, and the match boxes now each get their own
  row.
- The league's round-robin match list no longer fully rebuilds (and no longer resets its scroll
  position) when a winner is marked — only the affected row's text/color updates in place; the
  standings panel next to it still refreshes normally (it has no scrollbar to preserve).
- You can now re-click a decided match's winner to undo that result — and everything that depended
  on it unwinds with it (an auto-resolved bye can't be undone, since there's nothing to undo).
- **Bracket-engine correctness fix:** the previous bye-handling could, in some non-power-of-two
  brackets, advance a team into a later round before it had actually won a real game. Every match
  now tracks how many teams will *ever* structurally reach it, and only a match that will truly
  ever host one team auto-resolves as a bye — a real two-team game is never skipped. If you ran a
  tournament on v0.25 or earlier with byes, it's worth re-checking that bracket's results.

**Congratulations**
- Built out for real: shows the champion team, their captain, and their full roster (with assigned
  Mystery Hero roles/characters where available), plus Back (to the Bracket) and End buttons.

**Background**
- Every screen now shows the blurred background image through its own body, not just around the
  edges — previously the screen's own interior was an opaque solid color sitting on top of it.

## v0.25
**Drafting (formerly Seeding)**
- Screen header renamed to "Drafting".
- Rank selector widened so "Grand Master" / "One Above All" no longer clip.
- Rank filter is now **exact tier**: Gold shows only Gold players ("Any" shows all).
- Once a player is drafted, that slot's rank selector is locked (greyed) to their tier until they are undrafted.
- After a team's last open slot is filled, control moves to the first open slot of the next team (wrapping around), and the left panel scrolls to it.
- **Save / Continue now works.** Save writes the full draft (team names, drafted players, filters); Continue on the Greeting screen restores it. Every save (Seed / Spin / Bracket Setting) stores the complete state, and Continue jumps back to the stage it was saved at. Start now begins a truly fresh draft.
- Fixed: undrafting a slot didn't refresh that slot's own row until something else updated it.
- Platform icons (PlayStation / Xbox / PC) show on captain rows, drafted slots and the roster.

**Mystery Hero**
- Player card now shows the team name and captain, plus the player's platform.

**Bracket Settings**
- Seed order is a drag-and-drop list (▲/▼ buttons kept as a fallback); rows are built once and updated in place, so reordering or picking a format no longer rebuilds the screen.
- New buttons: Confirm (to the Bracket), Previous (back to the Mystery Hero screen), Save (state "Bracket Setting").

**Data / setup**
- `data/players.csv` is now the 56-player set with a new `platform` column (before `captain`, which stays last). 5-column files still load.
- Added `requirements.txt` (Pillow) and `run.bat` installs it automatically. Pillow was the likely reason the background image never appeared: it isn't part of Python's standard library.
- Background: wider glass margin (30px), lighter dimming, cooler tint, thin glass edge, and a more colorful default `background.png`. A console message now explains if Pillow is missing.

## v0.24
- **Bracket Settings** is now fully built: reorder the seed order with up/down arrows (top = seed 1,
  each row shows team name + captain), pick a format (Single Elimination / Double Elimination /
  League + Playoffs), and Start Tournament builds the bracket.
- **Bracket** is now fully built (`app/data/bracket.py` + `app/screens/bracket.py`):
  - Single elimination uses standard tournament seeding (1v8, 4v5, 2v7, 3v6, etc.) with automatic
    byes when the team count isn't a power of two.
  - Double elimination adds a losers bracket (standard alternating minor/major-round structure) and
    a Grand Final between the winners- and losers-bracket champions.
  - League + Playoffs runs a full round robin (with live standings) and, once every match is
    decided, "Generate Playoffs" seeds the top 4 teams into a single-elimination bracket.
  - The bracket renders as a zoomable (+/-), independently 2D-scrollable canvas tree with connector
    lines; click a team in any undecided match to mark them the winner, which automatically
    advances them (and, in double elimination, drops the loser into the losers bracket).
  - End Tournament unlocks once a champion is decided and moves on to Congratulations.
  - All bracket-generation and progression logic was verified with randomized simulations across
    single/double elimination and league play for team counts from 2 to 16 (including non-power-
    of-two counts with byes) - every run produced exactly one champion with no stuck states.

## v0.23
**Seeding**
- Assigning a player now auto-advances the active slot to the next empty slot in that team.
- If a slot's rank filter was "Any" when a player is assigned, it snaps to that player's rank tier.
- Clicking an already-filled slot again clears it, returning the player to the pool.
- Assigned players' preferred-role icons now show on the left (team) panel too.
- Interactions restyle existing widgets in place instead of rebuilding the whole screen; only an
  actual pool-membership change (assign/unassign/reset) rebuilds the roster list.
- Footer buttons moved to the bottom right, with Lock Seed farthest right.
- The player pool is sorted highest rank first whenever it's (re)built.

**Mystery Hero**
- Spinning no longer starts automatically - added a Spin button; Confirm is disabled until a spin
  has landed.
- Layout is centered both vertically and horizontally.
- During the character phase, the assigned role's icon flanks both sides of the reel.
- "DPS" renamed to "Duelist" everywhere (CSV role, UI labels, icon keys, role pool) - it's the same
  role the character roster JSON already used, so the old DPS/Duelist alias mapping is gone too.
- Player info panel is bigger and shows more: Twitch handle, peak rank, and preferred-role icons,
  in addition to name and progress.
- Heading restructured: "Role Spin"/"Character Spin" is now the top heading, team name is the
  subheading underneath it, and the "Mystery Hero" label above the heading was removed.

**App-wide**
- Added a blurred, dimmed background image layer (`app/ui/background.py`) behind the whole window
  for a frosted-glass feel - drop your own image at `assets/background.png` to use it. Note: plain
  tkinter can't make foreground panels truly see-through, so this renders one blurred+dimmed backdrop
  behind the window with the content inset over it, rather than true per-panel glass.

## v0.2
- **Fixed rank filtering** in Seeding. It now strips the 1/2/3
  subdivision and compares tiers as plain numbers (Bronze=1,
  Silver=2, Gold=3, Platinum=4, Diamond=5, Grand Master=6,
  Celestial=7, Eternity=8, One Above All=9). Selecting e.g. Platinum
  filters the roster to tier number >= 4, subdivision ignored on
  both sides. See `app/data/ranks.py`.
- **Added a slot-machine reel animation** to the Mystery Hero screen
  (`app/ui/slot_reel.py`). Candidate values scroll from the top of
  the reel down through a highlighted result window and land on the
  actual outcome; Respin/Confirm are disabled while it's spinning.

## v0.1
- Initial scaffold: folder structure, data loaders (CSV/JSON/rank
  logic/icons), save system, screen navigation.
- Fully working Greeting, Seeding, Select Tournament Type, and
  Mystery Hero (role + character spin, no animation yet).
- Bracket Settings, Bracket, and Congratulations still placeholders.
