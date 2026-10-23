# Hero Shooter Community Tournament

A Windows desktop app for running a community Hero Shooter tournament:
seed teams from a player roster, optionally scramble roles & heroes
("Mystery Hero"), then run the bracket.

## Setup (Windows)

1. Install Python 3.10+ from python.org. On the install screen, leave
   **"tcl/tk and IDLE"** checked (it's checked by default) — this is
   what the app's UI is built on, and it ships with the standard
   Windows installer, so no extra packages are required to run the app.
2. Double-click `run.bat` (or run `python main.py` from this folder). `run.bat` opens the app
   without leaving a command window behind. If the app ever fails to start, you'll get an error
   popup and the details are saved to `saves/crash.log`.

`run.bat` also installs **Pillow** and **pygame-ce** automatically the first time (Pillow draws the
glassy backgrounds, gradient buttons, icons and effects; pygame-ce powers optional background
music/click sounds). If you launch with `python main.py` instead, run
`python -m pip install -r requirements.txt` once. Both are optional: without Pillow the app falls
back to flat colors and plain buttons (platform icons show as text badges: PS / XB / PC); without
pygame-ce (or with no audio files in `assets/audio/`), the app is silent — no errors either way.
Nothing in the app ever calls out to the internet: every icon, font, picture and sound is a local file.

## Folder structure

```
RivalsCommunityTournament/
├── main.py                  entry point
├── run.bat                  Windows double-click launcher
├── CHANGELOG.md             what changed in every version
├── app/
│   ├── app_state.py          root window + screen navigation + shared state + toolbar
│   ├── data/
│   │   ├── ranks.py           rank tier system (Bronze..One Above All) + sorting
│   │   ├── players.py         player CSV loader
│   │   ├── roster.py          character roster JSON loader
│   │   ├── team.py            Team model (captain, slots, mystery-hero results)
│   │   ├── bracket.py         bracket generation/progression (single/double elim, league+playoffs)
│   │   ├── icons.py           role icon lookup with native-glyph fallback
│   │   ├── platforms.py       PlayStation / Xbox / PC normalisation + icon names
│   │   └── save_manager.py    save/load tournament progress
│   ├── screens/                one module per screen (see flow below)
│   └── ui/
│       ├── theme.py            light/dark palettes, accent colors, spacing grid, fonts
│       ├── text.py             every piece of on-screen wording + app_config.txt reader
│       ├── prefs.py            remembers light/dark between sessions (saves/prefs.json)
│       ├── fonts.py            registers the font files in assets/fonts/ for the app
│       ├── gfx.py              glass backgrounds, gradients, icons, sparkles (all drawn locally)
│       ├── widgets.py          gradient buttons, toolbar buttons, panels, chips, header bars, text measuring
│       ├── kit.py              drawing tools for canvas lists: scrolling canvas, badges, chips, rank tags, hover hints, pick list
│       ├── stage.py            base class every screen shares: background, header, grid, footer
│       ├── dialogs.py          the reset / unsaved-changes / saved pop-ups
│       ├── picker.py           the accent color picker (Greeting "Theme" button)
│       ├── player_icons.py     loads the role / platform icon pictures (cached)
│       ├── slot_reel.py        slot-machine reel animation (Mystery Hero)
│       ├── pop_anim.py         header "pop-in" animation (Greeting/Congratulations)
│       ├── popup.py            small transient info popup (Bracket captain-name popup)
│       └── audio.py            background music + click sounds (pygame-ce, optional)
├── data/
│   ├── players.csv            EDIT THIS — your player roster
│   └── characters.json        EDIT/REPLACE — Hero Shooter character roster
├── assets/
│   ├── app_config.txt         EDIT THIS — title, host, colors, fonts, volume and every piece of on-screen text
│   ├── icons/                 REPLACE — vanguard.ico / duelist.ico / strategist.ico / app.ico (taskbar icon)
│   ├── fonts/                 OPTIONAL — keep custom font files alongside the tournament folder
│   │   └── licenses/           their license files, if any
│   ├── backgrounds/           OPTIONAL — dark.png / light.png (or .jpg/.webp) to replace the generated background
│   └── audio/
│       ├── music/              DROP IN — one file per screen, see "Audio" below
│       │   └── licenses/        track license files, if any
│       └── sfx/                DROP IN — click.ogg/mp3/wav
│           └── licenses/        sound-effect license files, if any
└── saves/                     auto-created; holds the last save file and prefs.json
```

## Screen flow

Greeting → Drafting → Select Tournament Type → (Mystery Hero: Role
Spin → Character Spin, or straight through for Normal) → Bracket
Settings → Bracket → Congratulations.

Every screen after the Greeting has a **Home** button at the left end of the bottom row. It goes back
to the start screen after the unsaved-changes warning (OK to go, Cancel to stay).

The header of every screen after the Greeting shows a six-step tracker (Draft · Type · Spin · Seed ·
Bracket · Crown) with the current step lit. It's display only.

**Status of this build:**
- **Fully implemented:** Greeting, Drafting, Select Tournament Type, Mystery Hero, Bracket Settings,
  Bracket (single elimination, double elimination, and league + playoffs), and Congratulations.
  See CHANGELOG.md for the per-version details.
- Team and player counts are never typed in anywhere: they come from the number of captains in
  `data/players.csv`.

## Look and feel

- **Minimal and paper-like.** The window is one flat matte colour with a very faint grain over it, and
  every fill is flat: no gradients, no shine, no glow. Panels and section titles carry a plain thin rule.
- **Dark mode (default):** a cold near-black paper with fluorescent colours held inside a single
  green-to-purple range — mint accent, blue / purple / green roles, and eight team colours that walk that
  ramp. **Light mode:** warm paper with an apricot accent and muted warm pastels. Team names and player
  lists stay colourful and tellable apart in both modes.
- Everything is a plain rectangle (no rounded corners), laid out on one consistent 12-column grid with
  the same margins at every screen edge, so nothing clips or overlaps.
- The paper grain can be turned off with `Grain: off`. The old sparkle / cosmic-dust effect is off by
  default now; `Sparkles: on` brings it back.
- A small "Made by Mrit" watermark sits bottom-center on most screens, bottom-left on Drafting and
  bottom-right on the Greeting screen.
- **Background pictures:** put `dark.png` and/or `light.png` (`.jpg` / `.jpeg` / `.webp` / `.bmp` also work) into
  `assets/backgrounds/` and the app uses them (scaled to fill the window, edges cropped) in place of the generated
  background. A missing file just falls back to the generated one.

## Speed and smoothness

Windows paints every control (button, label, frame) as its own native window, so a screen built from
hundreds of them loads piece by piece and flickers when anything changes. The long lists and cards
(Drafting teams and roster, Mystery Hero lists and player card, Bracket Settings rows and format cards,
the league match list and standings, the Congratulations roster) are therefore **drawn directly on
canvases**: a click recolors or moves what changed instead of rebuilding anything, icons are cached
pictures, and a new screen is built and laid out before it is shown. The backgrounds for the other
color mode and for full screen / windowed — paper grain and all — are drawn ahead of time while the app
is idle, so toggling is quick. The big Greeting and Congratulations headings pop in once, half a second after you arrive.

## Toolbar (top-right, every screen)

Left to right: **Light/Dark**, **Mute/Unmute**, **Volume Down**, **Volume Up**, **Fullscreen** (Escape also
exits fullscreen). All five buttons are small, identical, perfectly square, tucked into the top-right
corner, and colored with the app's current accent color. Hover any of them for a hint.

- **Light/Dark** switches the whole app between the two looks without losing your place or anything
  you've picked. The app remembers your choice next time it opens (in `saves/prefs.json`); the
  `Start Mode:` line in `assets/app_config.txt` only decides the very first launch. The button is
  held back for a moment while a Mystery Hero spin is animating.
- Mute/volume control the optional background music and click sounds (see "Audio" below) — the buttons
  still work with no audio files present, they just have nothing to mute.

## Customizing the look

- **Theme button** (Greeting screen, top-left) opens a color picker that replaces the app's accent color
  everywhere in both modes (buttons, highlights, captain name labels, etc.) — set it with the R/G/B
  fields or type a hex code directly (they stay in sync either way), preview the swatch, then Apply.
- **Default accent colors:** `Theme Dark:` and `Theme Light:` in `assets/app_config.txt` set the starting
  accent of each mode (stock: yellow in dark, peach in light). A plain `Theme:` line overrides **both**,
  so if you keep a `Theme:` line (the shipped file has one) the stock yellow / peach never show; comment
  it out with a leading `#` to get them back. Colors can be hex (`#3FA7FF`, with or without the `#`) or
  plain names like `blue`. Keys aren't case-sensitive, `Theme = #3FA7FF` works too, and the file can be
  saved as plain UTF-8 or Notepad's UTF-16 "Unicode".
- **Start Mode / Grain / Sparkles:** `Start Mode: dark` or `light`; `Grain: on` or `off` for the paper
  texture over the background; `Sparkles: on` or `off` for the old star-field and dust (off by default).
- **Font:** uncomment and edit the `Font:` line in `assets/app_config.txt` to use a custom font
  family that's installed on the machine running the app (or dropped into `assets/fonts/`), in place of
  the default, app-wide.
- **Font Size:** uncomment and edit the `Font Size:` line (0.5–3.0) to scale every font up or down,
  on top of the automatic resolution scaling.
- **Per-screen fonts:** uncomment `<Screen> Heading Font:` / `<Screen> Body Font:` lines to give a
  specific screen its own font, overriding `Font:` just there — including the Greeting and
  Congratulations screens' big headings specifically. See the comments in `app_config.txt` for
  the full list of screen names and examples.
- **All on-screen text:** the bottom of `assets/app_config.txt` lists every heading, button label, hint,
  tooltip and pop-up message the app shows, each as a commented `# Key: built-in wording` line. Remove
  the `# ` and edit the wording to change it. Pieces in `{braces}` (like `{team}` or `{n}`) are filled in
  by the app, so keep them. `Title:` and `Host:` at the top work the same way.
- The bottom of the Greeting screen states the app's license and current version.
- **App icon:** drop an `app.ico` file into `assets/icons/` to have it show as the window/taskbar
  icon while the app runs, in place of the generic Python icon. If there's no `app.ico`, any other
  `.ico` in that folder that isn't one of the built-in role/platform icons is used instead.
  Optional — with none present, the default icon is used.

## Pop-ups

- **Reset** (Drafting) asks "Reset all data?" first and only resets if you press OK.
- **Save** (Drafting, Mystery Hero, Bracket Settings) shows a "Saved" notice with an OK button.
- **Home** (every screen except Greeting) shows the unsaved-changes warning ("...take you back to the
  start and reset all data from this tournament...") and only goes back to the Greeting screen on OK.
- **Unsaved changes:** every way of closing the app — **End** on the Greeting screen, **End** on the
  Congratulations screen, and the window's own close (X) button — first warns that unsaved work will be
  lost and only closes if you press OK. The Bracket screen's **End Tournament** button just moves on to
  Congratulations, so it has no warning.

## Audio (optional)

Drop files into `assets/audio/music/` for looping background music per screen, named after the
screen: `greeting`, `seeding` (Drafting), `tournament_type`, `mystery_spin` (Mystery Hero),
`bracket_settings`, `bracket`, `congrats` — e.g. `greeting.ogg`. Drop `click.ogg`/`.mp3`/`.wav` into
`assets/audio/sfx/` for a button-click sound. Each file can be `.ogg`, `.mp3` or `.wav` (tried in
that order); any screen or the click sound with no matching file is simply silent. Requires the
optional `pygame-ce` package; with it missing, or no audio files present, the app runs normally and
stays silent. Keep each file's license (if any) in that folder's `licenses/` subfolder.

Switching screens, or a track looping back to its start, cuts straight to the next track (no fade).
**Default volume:** uncomment and edit the `Volume:` line in `assets/app_config.txt` (1–10) to set
the volume the app starts at — the toolbar's Volume Up/Down buttons still adjust it from there, per
session.

## Editing the data files

- `data/players.csv` — semicolon-separated:
  `in-game-name;twitch/yt_name;peak-rank;preferred-roles;platform;captain`
  - `in-game-name` and `twitch/yt_name` are both **mandatory** — a row missing either
    one fails to load. The Twitch/YouTube name is shown as-is everywhere in the app (no `twitch.tv/`
    formatting) as the player's main identifier, with their in-game name shown underneath (or beside
    it, on compact rows) as a smaller subheading — put whatever handle, Twitch, YouTube, or
    otherwise, you want displayed front-and-center
  - `preferred-roles` is comma-separated, 1–3 of `Vanguard`, `Duelist`, `Strategist`
  - `peak-rank` is e.g. `Platinum 2`, or `Eternity` / `One Above All` (no subdivision)
  - `platform` is `PlayStation`, `Xbox` or `PC` (blank = no icon)
  - `captain` is `true`/`false` and must stay the **last** column - the number of `true` rows is
    your team count (the app derives every team and player count from this file)
  - older 5-column files (no platform) still load, as long as every row has both names filled in
- `data/characters.json` — replace with an updated roster export as
  Hero Shooter adds characters; the app reads it fresh each launch.

## Rank filtering & search (Drafting)

A slot's rank filter matches the **exact tier** - the 1/2/3 subdivision is
ignored. Selecting "Gold" **hides** every player who isn't Gold (Gold 1, 2
and 3 all show); "Any" shows everyone. Once a player is drafted, that slot's
selector is locked to their tier until they are undrafted. (Tier numbers,
used for sorting: Bronze=1 … Grand Master=6, Celestial=7, Eternity=8, One
Above All=9.)

Each slot's rank picker is a small pick list (Any plus every tier). A search box above the roster narrows it to names matching what's typed — it matches a plain
substring or the typed letters in order (e.g. "jsm" matches "JohnSmith") against **either** the
player's Twitch/YouTube name or their in-game name, and combines with the rank filter above. Each
drafted slot shows that player's preferred-role icon(s) alongside their platform icon.

## Mystery Hero

The screen is split into three evenly sized parts on the grid: the "Sorted" list on the left (3 columns),
the spin area in the middle (6 columns, exactly centered) and the "Upcoming" list on the right (3 columns).
Fully-sorted teams are listed in the left "Sorted" pane; teams still waiting are in the right
"Upcoming" pane. Names are aligned left and the captain's **C** sits right after the captain's name;
each row ends with the character (once picked) and a role icon, and all the icons line up in one
straight column at the right edge (before a player has spun, the Upcoming list shows their preferred
roles instead). You can track tournament-wide progress without leaving the spin screen. **Click any team in "Upcoming" to spin for it** - the center panel switches to that
team immediately. If you switch away from a team that's partway through its role/character spins,
that team's progress is wiped and it goes back to waiting in "Upcoming", so switching mid-series is
a deliberate restart, not a pause. Once every team is fully sorted, the center panel shows a plain
"Done" message. **Spin** runs a smooth, time-based reel that eases to a stop on the result, and
**Confirm** locks it in (both buttons are the same size). **Back** returns to Select Tournament
Type, resetting every team's spin progress (re-picking Mystery Hero from there starts the spins over
anyway).

## Bracket Settings

Drag the seed rows to reorder (top = seed 1) and pick the bracket type from three cards, each with a
small diagram. **Back** returns wherever this screen was reached from: Mystery Hero if you went
through Role/Character Spin, or Select Tournament Type if you picked Normal and skipped straight here.
With fewer than two teams the screen says so and won't start.

## Bracket

Only a team's actual starting position is shown up front; a later round's
match only appears once a team has actually reached it. **Single-click** a team's name for a quick
popup with their captain's name — it closes on its own after a moment, or immediately if you click
anywhere else; **double-click** an undecided match to mark that team the winner
(it advances automatically, and in double elimination drops the loser into the losers bracket), and
double-click a decided match's winner again to undo it (an auto-resolved bye can't be undone). The
league stage's round-robin match list updates in place as results come in, so marking a winner never
resets its scroll position, and the standings panel sits level with it. A slot that is still waiting
for a team says "TBD"; "BYE" is only used for a real bye.

The tree **fits itself to the window** when it first appears and again when it grows (for example when
the losers bracket shows up), never zooming in past 100%. After that:
- **−/+** buttons just above the footer zoom out/in in 10% steps (35%–250%); once you zoom by hand the
  app stops auto-fitting.
- **Drag** empty canvas to pan, use the **mouse wheel** to scroll up/down and **Shift + wheel** to scroll
  sideways.

The header line shows how many matches are decided ("n of m matches decided") and, once there is one,
the champion. **End Tournament** unlocks when the tournament is complete and moves on to
Congratulations.

## Congratulations

Shows the winning team's name, captain, and roster in a tidy three-column grid. In a **Mystery Hero**
tournament each tile shows only the class icon of the character that player was given, with that
character's name under the player's name. In a **Normal** tournament the line under the name is blank
and the tile shows the player's preferred role icons. Only each player's Twitch/YouTube name is shown
here (no in-game-name subheading, unlike the other screens). **Back** returns to the bracket; **End** closes the app after the unsaved-changes warning.

## Not yet verified

This build was assembled and checked in an environment with no Windows and no screen, so the following
have only been verified by running the app on your own computer: window and layout rendering at your
resolution, font loading from `assets/fonts/`, the taskbar icon, the translucent dimming behind pop-ups,
spin smoothness at your real frame rate, audio, tooltips, and how the paper grain reads on your monitor. The speed-ups described under "Speed and
smoothness" were measured in the build environment only; how fast they feel on your machine (including the
full screen switch and light/dark toggle) is for you to judge.
