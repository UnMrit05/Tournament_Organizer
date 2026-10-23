# Changelog

## v0.43
**Changed - new paint: minimal, paper-like, flat and matte** (look only; no layout and no operational logic changed)
- **Nothing moved.** Every rect, font size, margin and alignment is exactly as it was in v0.42. The whole
  release is `app/ui/theme.py` and `app/ui/gfx.py`, plus the handful of places that still had a colour
  written into them.
- **Paper ground.** The window is now one flat matte colour with a very faint grain over it, instead of
  the glass gradient and its coloured glows. The grain is drawn once per window size and cached with the
  background, so it costs nothing while the app runs. Turn it off with `Grain: off` in
  `assets/app_config.txt`. Your own `assets/backgrounds/dark.*` / `light.*` still replace it.
- **Flat and matte everywhere.** Button faces, team headers, rank blocks, the trophy medal, the reel band,
  pop-up headers and the little section swatches lost their gradients and are now one colour each. The
  white highlight line along the top of buttons, the sparkle glint on the primary buttons and the
  four-colour aurora trim are gone; panels and section titles now carry a plain thin rule. Hovering a
  button shades it very slightly instead of lighting it up.
- **Dark mode: cold, fluorescent, green to purple.** Ground `#0F1216`, ink `#E9EEF2`, accent mint
  `#4FE6C4`. Roles are blue `#5E9CFF`, purple `#B07BF5` and green `#4FE8A0`; Reset is purple and
  Confirm is blue. The eight team colours walk a green-to-purple ramp and alternate its two halves, so
  two cards side by side never look alike. Rank tiers run the same ramp in order, deep green up to pale
  lilac (so Bronze, Silver and Gold are no longer metal-coloured).
- **Light mode: warm, pastel.** Warm paper `#F2ECE1`, ink `#2B2620`, apricot accent `#E9B98D` with a
  burnt-peach `#8A4E22` for accent text. Roles are dusty blue, terracotta and sage; the eight team
  colours are muted warm pastels and the rank tiers are their warm equivalents.
- **Sparkles are off by default.** The star-field and cosmic dust don't suit a paper look. They are still
  there if you want them: `Sparkles: on` in `assets/app_config.txt`.
- **Colours that were written into screens are now part of the palette.** The band above the player
  roster, the two Tournament Type cards, the compass behind the Start panel, the pop-up headers, the
  Theme picker's preset swatches and the dark ink used on coloured headers all read from the palette, so
  they follow the mode and your accent instead of staying fixed.

**Worth knowing**
- Your `assets/app_config.txt` has a plain `Theme: #32a852` line, and that still overrides both stock
  accents. The mint and apricot accents only show once that line is removed or commented out.
- New settings appended to `assets/app_config.txt` as comments: `Grain: on`. `Sparkles` now defaults to
  `off`.

**Not verified** (the build environment has no Windows): how the grain reads on your monitor at your
resolution and scaling, whether the flat faces look right with your own fonts, and the first-draw cost of
the grain on your machine (it is drawn once per size and pre-drawn while the app is idle, as before).


## v0.42
**Changed - performance and smoothness first** (no operational logic changed)
- **Screens open in one go.** Drafting, Mystery Hero, Bracket Settings, the league view and the
  Congratulations roster used to be built from hundreds of separate controls (about 1,500 on Drafting),
  and Windows paints those one by one, which is the "element by element" loading you saw. Those lists and
  cards are now drawn on a handful of canvases (Drafting 12 controls, Mystery Hero 14, Bracket Settings 8,
  league 8, Congratulations 4) and are drawn at their final size before the screen is shown.
- **Clicking no longer reloads things.** Selecting a slot, a player or a team, changing a rank filter,
  searching, and Confirm on Mystery Hero only recolor, move or redraw what changed. Icons are cached
  pictures, so nothing flashes on Confirm and the central player card updates instantly.
- **Light/dark toggle is quick.** The same fewer-controls change, plus cached text measurements and
  pre-drawn backgrounds for both modes, makes switching a single short step instead of a full rebuild.
  Your place, selections, search words and scroll positions are kept.
- **Full screen / windowed** just re-lays the screen out. The matching backgrounds are drawn ahead of
  time while the app is idle, so there is no repaint flash.
- **Pop animation** on the Greeting and Congratulations headings now waits half a second after you arrive,
  and only plays when you arrive - never when you switch full screen/windowed or light/dark.
- **New Home button** at the left of the bottom row on every screen except Greeting. It takes you back to
  the start and shows the unsaved-changes warning first (OK to go, Cancel to stay).

**Drafting**
- In-game names under the player names are a little smaller so they never touch the box edge.
- The "8 captains -> 8 teams" box is gone.
- The rank picker on each slot is a small pick list (same choices as before).

**Mystery Hero**
- The screen is now three evenly sized parts: left list (3 grid columns), center (6) and right list (3),
  so the center really is in the middle.
- Player names are aligned left; the captain's **C** sits right after the captain's name.
- On the left (Sorted) list each row reads `player name ... character <class icon>`, and all class icons
  sit in one straight column against the right edge. The Upcoming list uses the same layout.

**Congratulations**
- Mystery Hero tournaments: each tile shows only the class icon of the character that player was given,
  with that character's name under the player's name (the preferred-roles text is gone).
- Normal tournaments: the line under the name is blank and the player's preferred role icons show as before.

**Housekeeping**
- New `app/ui/kit.py` (scrolling canvas, drawn badges / chips / rank tags, hover hints, pick list). Removed
  the unused `scrollable.py`, and the old widget helpers from `player_icons.py` and `widgets.py`.
- New text keys `Button Home` and `Home Popup Text` (appended to `assets/app_config.txt` as comments).
  `Drafting Teams Count` is no longer used.

**Not verified** (the build environment has no Windows): real-machine speed and smoothness, the full
screen flash on your monitor, the mouse wheel over the new lists, the rank pick list and hover hints, the
Home flow with the real pop-up, and the pop animation timing. In the build environment, opening Drafting
went from about 750 ms to about 40 ms and a light/dark switch from a full rebuild to 20-80 ms, but that is
not a Windows measurement. Please run it once and report anything that looks off.

## v0.41
**Changed - full graphics and UI overhaul** (look and layout only; no operational logic changed)
- **New look.** Dark mode (default) is a glassy black gradient with yellow highlights; light mode is a
  pearl-white glass with a peach accent. Player lists and team-name panels are bright and colorful in
  both modes, boxes carry highlight colors and buttons carry gradients. Every element is a plain
  rectangle, laid out on one 12-column grid with the same margins at every screen edge, so nothing
  clips or overlaps. A faint sparkle / cosmic-dust effect floats behind the screens.
- **Light/dark toggle** added to the top-right toolbar (now five buttons: Light/Dark, Mute, Volume Down,
  Volume Up, Fullscreen). The choice is remembered in `saves/prefs.json`; switching keeps your place and
  everything you've picked.
- **Header step tracker** (Draft · Type · Spin · Seed · Bracket · Crown) on every screen after the Greeting.
  Display only.
- **Every screen redrawn:** Greeting, Drafting, Select Tournament Type (two big cards), Mystery Hero
  (player card, reel, pool chips, Sorted / Upcoming panes), Bracket Settings (seed rows + three format
  cards with diagrams), Bracket (tree and league views) and Congratulations (medal, rays and a
  three-column roster grid; no separate "Tournament Complete" title).
- **Smoother, less flashy.** Screens are built once and updated in place, so selecting and deselecting
  no longer reloads the lists. The Mystery Hero reel is now time-based and eases to a stop. Spin and
  Confirm are the same size; Reset, Save and Lock Seed are the same size.
- **Pop-ups:** Reset asks for confirmation first; every Save shows a "Saved" notice with OK; every way of
  closing the app (Greeting End, Congratulations End, the window's X) shows an "Unsaved changes" warning
  and only closes on OK. The Bracket's End Tournament only moves to Congratulations, so it has no warning.
- **Bracket navigation:** the tree fits itself to the window at first and when it grows (never above 100%),
  zoom buttons work in 10% steps, drag empty canvas to pan, mouse wheel / Shift + wheel to scroll.
  The league standings panel lines up with the match list. A header line shows matches decided and the
  champion.
- **Config:** every heading, button, hint, tooltip and pop-up message is now editable from
  `assets/app_config.txt` (the full list is appended there as commented lines). New settings:
  `Start Mode`, `Theme Dark`, `Theme Light`, `Sparkles`. Optional `assets/backgrounds/dark.*` and
  `light.*` replace the generated backgrounds. A plain `Theme:` line still overrides both accents.
- **New modules in `app/ui/`:** `text.py`, `prefs.py`, `fonts.py`, `gfx.py`, `widgets.py`, `stage.py`,
  `dialogs.py`, `picker.py`. All icons, fonts, backgrounds and sounds are local files; the app makes no
  external calls.

**Fixed**
- **Bracket: misleading "BYE".** A slot that was simply waiting for a team used to say BYE; it now says
  TBD, and BYE is only shown for a real bye.

**Not verified** (the build environment has no Windows and no screen): window rendering at your
resolution, font loading, the taskbar icon, pop-up dimming, spin smoothness at your frame rate, audio and
tooltips. Please run it once and report anything that looks off.

## v0.40
**Fixed**
- **Drafting: captain-row icons.** The role icons next to a captain's name floated at a different
  height from their platform icon. The platform and role icons now sit together in one neat row
  beside the name, with the in-game name underneath.

## v0.36
**Fixed**
- **Default theme from `app_config.txt` not loading.** The config reader was strict about the file's
  exact format, so common real-world variations were silently ignored (or crashed): a file saved by
  Notepad as UTF-16 or with a BOM, `Theme : #3FA7FF` / `Theme = #3FA7FF` spacing, quotes, a trailing
  `# note`, 3-digit hex, or a color name. All of those now work (and every other setting - Title,
  Host, Font, Scale, Volume - uses the same tolerant reader). An invalid color is ignored instead of
  crashing. I couldn't run the Windows UI here, so if your `Theme:` line still doesn't take effect,
  send me the exact line.
- **Taskbar icon.** The app only looked for a file named exactly `app.ico`; it now falls back to any
  other `.ico` in `assets/icons/` that isn't one of the built-in role/platform icons. It also gives
  the app its own Windows taskbar identity (otherwise Windows groups it under Python's icon) and
  applies the icon to every window, with a Pillow-based backup if the `.ico` can't be loaded directly.
- **Toolbar buttons are now truly square** on every screen. They were sized in "characters x lines",
  which can't be square; they're now an exact pixel square (same size whatever the symbol on them).

**Changed**
- **No leftover command window.** `run.bat` now launches with `pythonw` and closes its own window
  straight away; the Pillow/pygame-ce check only installs when something is missing, so launching is
  faster too. If the app crashes on startup you get an error popup and the details are saved to
  `saves/crash.log`.
- **Code comments rewritten.** All version/history comments are gone from every source file. Each
  file now starts with a brief description, and every class, method and function has a short,
  informal comment saying what it does. (No behavior changes from this.)

## v0.35
**Fixed**
- **Mystery Hero: toolbar/pane overlap.** The "Upcoming" pane in the top-right didn't leave any
  clearance for the toolbar above it - unlike every other screen, this one has no top heading to
  push its content down, so the pane's header sat in the same space as the Mute/Volume/Fullscreen
  buttons. This screen's content now starts with real top margin, clear of the toolbar.

**Congratulations**
- Only the Twitch/YouTube name is shown for the captain and each roster player now (no in-game-name
  subheading underneath).
- Fixed the role icons/detail text beside each roster row drifting out of alignment with the name
  next to them - they were centering against the old two-line name+subheading stack instead of
  sitting flush with it; dropping the subheading (above) fixed this too.

**Audio**
- Removed the v0.34 crossfade engine - music switches instantly again on screen change or loop
  restart (plain `pygame.mixer.music`, one stream, hard cut, same as pre-v0.34). The default-volume
  config option and mute/volume toolbar controls are unaffected.

## v0.34
**Fixed**
- **Bracket stage-label overlap, for real this time.** The v0.32 fix added more margin, but the
  actual cause was that the bracket canvas's pixel geometry (box size, row/column gaps, label
  heights, top margin) was only scaled by the user's zoom level, not by the screen-resolution scale
  that the label *text* was already being scaled by internally — so on most displays the text grew
  past the fixed-pixel space reserved for it. The canvas geometry is now scaled by both, so the text
  and the space around it grow together at every resolution and zoom level.
- **Bracket: double-clicking a team name no longer also opens the captain popup.** A single click now
  waits a beat before opening the popup, so a following second click (completing a double-click) can
  cancel it first - the popup only appears for an actual single click, as intended.

**Drafting**
- On both sides of the screen, every player's **Twitch/YouTube name is now the main identifier**,
  with their in-game name shown underneath (or beside it, on the compact team-slot rows) as a
  smaller, fainter subheading.
- The search box now matches either name, not just the in-game name.
- The sample `data/players.csv` now has a Twitch/YouTube name filled in for all 56 players.
- The captain's row no longer shows "- locked" after their rank - just the rank, still uneditable.

**All screens**
- The Twitch/YouTube name is now the main identifier shown for players and captains everywhere (not
  just Drafting) - Mystery Hero, Bracket, and Congratulations all pick this up automatically.
- `in-game-name` and `twitch/yt_name` are both mandatory in `data/players.csv` now; a row missing
  either one fails to load with a clear error instead of silently showing a blank/fallback name.

**Navigation**
- Mystery Hero's Back button now returns to Select Tournament Type (was Drafting), still resetting
  every team's spin progress.
- Bracket Settings' Back button now returns wherever the screen was reached from - Mystery Hero or
  Select Tournament Type - instead of always going back to Mystery Hero.
- Every "Previous" button across the app is now labeled "Back".

**Audio**
- Music now cross-fades instead of cutting: both when switching to a different screen's track, and
  when a track reaches its end and loops back to the start. The fade is short by design.
- New optional `Volume:` line (1-10) in `assets/app_config.txt` sets the default/startup music
  volume; the toolbar's Volume Up/Down buttons still adjust it per session from there.

**Toolbar**
- The four top-right buttons (Mute, Volume Down, Volume Up, Fullscreen) are now smaller, square, and
  colored with the app's current accent color instead of plain white/gray text.

**Customization**
- New optional `app.ico` file in `assets/icons/` is used as the window/taskbar icon while the app
  runs, in place of the generic Python icon.

## v0.32
**Fixed**
- **Role icons never actually loaded.** On every screen, a player's preferred-role icons were only
  ever drawn as the plain text/glyph fallback — the code never tried loading the real `.ico` files
  from `assets/icons/` the way platform icons already did. They now load the same way platform icons
  do (falling back to the glyph only if the file/Pillow is missing).
- **Drafting:** a drafted slot's preferred-role icons weren't actually visible — the icon row was
  built but never packed into the slot, so only the platform icon ever showed. Fixed.
- **Accent-color hex code:** typing a hex code into the Theme picker and clicking Apply without
  first pressing Enter or tabbing out of the hex field silently discarded the typed value and
  applied the stale R/G/B fields instead. Apply now always commits the hex field first.
- **Congratulations screen was showing fully blank.** The v0.31 firework animation is removed
  (see "Congratulations" below) — this was the cause.

**Drafting**
- A fuzzy search box above the player roster narrows it to matching names as you type — matches a
  plain substring or the typed letters in order (e.g. "jsm" matches "JohnSmith"), and combines with
  the existing rank-tier filter.
- Drafted slots now correctly show the player's preferred-role icon(s) next to their platform icon
  (see "Fixed" above).
- The "Made by Mrit" watermark moved to bottom-left on this screen (was bottom-right).

**Mystery Hero**
- Removed the flanking role-glyph icons on either side of the spin reel.
- In the right-hand "Upcoming"/"Sorted" panes, each player's role icon(s) moved to the right side of
  their name (previously on the left, where multiple icons could overlap the name). The icons now
  actually load from `assets/icons/` instead of showing only the glyph fallback.

**Bracket**
- Team-name text in each match box is smaller (0.6x the previous size) so longer names fit more
  comfortably.
- The whole bracket tree now has extra top clearance, so round/section labels like "Quarterfinal" /
  "Semifinal" never sit against the match boxes below them.
- The single-click captain popup now also dismisses immediately on a click anywhere outside it
  (previously it only closed after a short timer or when a new popup replaced it).
- The "Made by Mrit" watermark moved to bottom-left on the Bracket Settings screen (was bottom-right;
  the Bracket screen itself is unchanged, still bottom-center).

**Congratulations**
- Removed the v0.31 looping firework animation — it was leaving this screen fully blank for some
  setups. `app/ui/fireworks.py` is removed, since nothing else used it.

**Customization**
- `assets/app_config.txt` (renamed from `tournament_info.txt` — see "Renamed" below) supports a new
  optional `Theme:` line (a hex color) to set the app's default/startup accent color, instead of the
  built-in gold.

**Dependencies**
- Switched from `pygame` to the actively-maintained `pygame-ce` fork in `requirements.txt` (same
  `import pygame` API, so no code changes were needed beyond the dependency name).

**Renamed**
- `assets/tournament_info.txt` is now `assets/app_config.txt`. Every place that reads it by name was
  updated to match (the app's title/host/scale/font/theme settings all still work the same way,
  just from the renamed file).

**Removed**
- The `README.txt` files inside `assets/icons/`, `assets/fonts/`, `assets/audio/music/`, and
  `assets/audio/sfx/` are gone (their `licenses/` subfolders and the README files inside those are
  unaffected). The filenames the app looks for in `assets/audio/music/` and `assets/audio/sfx/` are
  now documented directly in README.md's "Audio" section instead.

## v0.31
**Watermark**
- The "Made by Mrit" watermark now sits wherever it can't overlap anything: bottom-right on
  Drafting and Bracket Settings, bottom-center (just above the footer) on Bracket and Mystery Hero.
  It's also smaller and noticeably fainter now (both the text and the chip behind it).

**Mystery Hero**
- The left pane is now labeled "Sorted" (was "Already spun").
- You now pick which team to spin for — click any team in the "Upcoming" pane to make it the active
  one. Switching to a different team while one is partway through its spins resets that team's
  progress (it goes back to "Upcoming").
- Confirming a spin no longer rebuilds the side panes from scratch — only the row that changed
  updates, so the screen doesn't blink/flash on every click.
- The player-detail panel now shows the name from the CSV's `twitch/yt_name` column directly,
  instead of formatting it as a twitch.tv link.
- Once every team is sorted, the checkmarks in the player card and the reel are gone — it's a plain
  "Done" message, centered in its own box, both horizontally and vertically.
- Side-pane team boxes and their rows are smaller, so more fits on screen.

**Drafting**
- The player's platform icon next to a drafted slot's name is a touch bigger, matching the rest of
  the app's icon sizing.
- `data/players.csv`'s twitch/YouTube column is now headed `twitch/yt_name` (same position, still
  the 2nd column) to reflect that it isn't Twitch-only; the dummy roster now has exactly 8 captains.

**Bracket**
- Reverted the v0.30 scrollable/auto-fit-to-screen canvas — team names were shrinking past
  readability whenever it zoomed out to fit the window. Zoom in/out is still available (still
  continuous, not fixed steps) but is manual only now; the Fit button, auto-fit-on-open, and the
  scrollbars are gone. The zoom controls moved to their own row just above the footer buttons,
  bottom-center.
- **Fixed:** in single elimination, the Final match's round label incorrectly read "Semifinal" (an
  off-by-one in the round-numbering math). It now correctly reads "Final".
- The single-click captain-name popup and double-click winner-select/undo are unchanged.

**Customization**
- The accent-color picker (Theme button, Greeting screen) now also takes a hex code directly, kept
  in sync with the R/G/B fields either way.
- `assets/tournament_info.txt` supports an optional `Font Size:` multiplier (0.5–3.0, on top of the
  automatic resolution scaling) and optional per-screen `<Screen> Heading Font:` / `<Screen> Body
  Font:` lines — including dedicated heading-font lines for the Greeting and Congratulations
  screens specifically — that override the app-wide `Font:` just for that screen.
- Volume buttons reordered to Mute/Unmute, Volume Down, Volume Up (left to right), and the whole
  top-right toolbar (those three plus Fullscreen) is smaller and tucked further into the corner so
  it clears the Mystery Hero screen's side panes.
- New `assets/fonts/` folder (for keeping custom font files with the tournament folder), and a
  `licenses/` subfolder under each of `assets/fonts/`, `assets/audio/music/`, and `assets/audio/sfx/`.

**Congratulations**
- A small looping 8-bit-style firework animation now plays on the left and right edges of the
  screen (drawn procedurally, no video/image files needed).

**Terminology**
- README.md and the sample `tournament_info.txt` now say "Hero Shooter" instead of "Marvel
  Rivals"/"Rivals".

## v0.30
**Customization**
- `assets/tournament_info.txt` now also accepts an optional `Font:` line to use a custom font
  family (must be installed on the machine running the app) in place of the default Segoe UI-based
  faces everywhere in the app — leave it commented out for the default look.
- New Theme button (top-left of the Greeting screen) opens an RGB picker that replaces the app's
  accent color (previously a fixed gold) everywhere — buttons, highlights, captain labels, etc. —
  with a live preview swatch before you apply it.

**Platform icons**
- Platform icons (PlayStation/Xbox/PC) are bigger across the app and now scale with screen
  resolution like everything else (previously they stayed a fixed pixel size regardless of your
  monitor).

**Drafting**
- Editing a team's name now reliably sticks: it's committed the moment you hit Save or Lock Seed,
  and every later screen (Mystery Hero, Bracket Settings, Bracket, Congratulations) uses the name
  you typed.

**Mystery Hero**
- New two-pane layout: already-finished teams are listed on the left, teams still waiting their
  turn on the right, each showing per-player assigned roles/characters (or preferred roles if not
  yet spun) and the captain's name — so you can see tournament-wide progress without leaving the
  spin screen.

**Bracket**
- Zoom is now continuous (drag anywhere between min/max instead of a few fixed steps), plus a new
  Fit button, and the view automatically zooms to fit the whole bracket on screen the moment it
  opens.
- Single-click a team's name to see a quick popup with their captain's name; double-click to record
  them as the winner, and double-click again to undo it (an auto-resolved bye still can't be
  undone). This replaces the old single-click-decides behavior.

**Audio**
- Background music: drop an audio file named after a screen (e.g. `greeting.ogg`) into
  `assets/audio/music/` and it loops automatically while that screen is open — see the README
  there for the full list of screen names and supported formats (.ogg/.mp3/.wav).
- Button clicks now play a sound if you provide one at `assets/audio/sfx/click.*`.
- New toolbar in the top-right (next to Fullscreen): Mute/Unmute and Volume Up/Down controls,
  uniformly sized and laid out so nothing overlaps.
- Requires the optional `pygame` package (see `requirements.txt`); with no audio files, no pygame,
  or no sound card, the app runs exactly as before — totally silent, no errors.

**Polish**
- The "Congratulations!" header and the Greeting screen's title now pop in with a little bounce
  when their screen opens, instead of appearing instantly.
- A small "Made by Mrit" watermark now sits in the bottom-right corner of every screen.
- The Greeting screen now states the app's license and version number at the bottom
  ("Open-source software (MIT License) — v0.30").

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
