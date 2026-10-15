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

`run.bat` also installs **Pillow** and **pygame-ce** automatically the first time (Pillow powers the
`.ico` icons, pygame-ce powers optional background music/click sounds). If you launch with
`python main.py` instead, run `python -m pip install -r requirements.txt` once. Both are optional:
without Pillow, platform icons show as text badges (PS / XB / PC); without pygame-ce (or with no audio
files in `assets/audio/`), the app is silent — no errors either way.

## Folder structure

```
RivalsCommunityTournament/
├── main.py                  entry point
├── run.bat                  Windows double-click launcher
├── app/
│   ├── app_state.py          root window + screen navigation + shared state
│   ├── data/
│   │   ├── ranks.py           rank tier system (Bronze..One Above All) + sorting
│   │   ├── players.py         player CSV loader
│   │   ├── roster.py          character roster JSON loader
│   │   ├── team.py            Team model (captain, slots, mystery-hero results)
│   │   └── bracket.py         bracket generation/progression (single/double elim, league+playoffs)
│   │   ├── icons.py           role icon lookup with native-glyph fallback
│   │   ├── platforms.py       PlayStation / Xbox / PC normalisation + icon names
│   │   └── save_manager.py    save/load tournament progress
│   ├── screens/                one module per screen (see flow below)
│   └── ui/
│       ├── theme.py            shared colors/fonts/accent color (plain black background)
│       ├── scrollable.py       independently-scrollable frame widget
│       ├── player_icons.py     role glyphs + platform badge widgets
│       ├── slot_reel.py        slot-machine reel animation (Mystery Hero)
│       ├── pop_anim.py         header "pop-in" animation (Greeting/Congratulations)
│       ├── popup.py            small transient info popup (Bracket captain-name popup)
│       └── audio.py            background music + click sounds (pygame-ce, optional)
├── data/
│   ├── players.csv            EDIT THIS — your player roster
│   └── characters.json        EDIT/REPLACE — Hero Shooter character roster
├── assets/
│   ├── app_config.txt         EDIT THIS — title, host, and optional Scale:/Font:/Theme:/Volume:/font overrides
│   ├── icons/                 REPLACE — vanguard.ico / duelist.ico / strategist.ico / app.ico (taskbar icon)
│   ├── fonts/                 OPTIONAL — keep custom font files alongside the tournament folder
│   │   └── licenses/           their license files, if any
│   └── audio/
│       ├── music/              DROP IN — one file per screen, see "Audio" below
│       │   └── licenses/        track license files, if any
│       └── sfx/                DROP IN — click.ogg/mp3/wav
│           └── licenses/        sound-effect license files, if any
└── saves/                     auto-created; holds the last save file
```

## Screen flow

Greeting → Drafting → Select Tournament Type → (Mystery Hero: Role
Spin → Character Spin, or straight through for Normal) → Bracket
Settings → Bracket → Congratulations.

**Status of this build:**
- **Fully implemented:** Greeting, Drafting, Select Tournament Type, Mystery Hero (see CHANGELOG
  for v0.2/v0.23/v0.30/v0.31/v0.32/v0.34/v0.35/v0.36 details), Bracket Settings, Bracket (single
  elimination, double elimination, and league + playoffs - see the
  v0.24/v0.26/v0.30/v0.31/v0.32/v0.34 changelog entries), and Congratulations.
- Every screen scales to the screen's resolution against a plain black background. A small, faint
  "Made by Mrit" watermark sits tucked in a corner that's always clear of that screen's own buttons
  — bottom-right on most screens, bottom-center (just above the footer) on Bracket and Mystery Hero,
  and bottom-left on Drafting and Bracket Settings.

## Toolbar (top-right, every screen)

Left to right: **Mute/Unmute**, **Volume Down**, **Volume Up**, **Fullscreen** (Escape also exits
fullscreen). All four buttons are small, identical, perfectly square, tucked into the very corner
without overlapping, and colored with the app's current accent color (see "Customizing the look" below) so they match
whatever theme is active. Mute/volume control the optional background music and click sounds (see
"Audio" below) — the buttons still work with no audio files present, they just have nothing to mute.

## Customizing the look (Greeting screen)

- **Theme button** (top-left) opens a color picker that replaces the app's accent color everywhere
  (buttons, highlights, captain name labels, etc.) — set it with the R/G/B fields or type a hex code
  directly (they stay in sync either way), preview the swatch, then Apply.
- **Default theme:** uncomment and edit the `Theme:` line in `assets/app_config.txt` (a hex color
  like `#3FA7FF`, with or without the `#`, or a plain color name like `blue`) to set the accent
  color the app starts with, instead of the built-in gold — the Theme button can still change it
  per-session from there. Keys aren't case-sensitive, `Theme = #3FA7FF` works too, and the file
  can be saved as plain UTF-8 or Notepad's UTF-16 "Unicode".
- **Font:** uncomment and edit the `Font:` line in `assets/app_config.txt` to use a custom font
  family that's installed on the machine running the app, in place of the default, app-wide.
- **Font Size:** uncomment and edit the `Font Size:` line (0.5–3.0) to scale every font up or down,
  on top of the automatic resolution scaling.
- **Per-screen fonts:** uncomment `<Screen> Heading Font:` / `<Screen> Body Font:` lines to give a
  specific screen its own font, overriding `Font:` just there — including the Greeting and
  Congratulations screens' big headings specifically. See the comments in `app_config.txt` for
  the full list of screen names and examples.
- The bottom of the Greeting screen states the app's license and current version.
- **App icon:** drop an `app.ico` file into `assets/icons/` to have it show as the window/taskbar
  icon while the app runs, in place of the generic Python icon. If there's no `app.ico`, any other
  `.ico` in that folder that isn't one of the built-in role/platform icons is used instead.
  Optional — with none present, the default icon is used.

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

- `data/players.csv` — semicolon-separated (ships with 56 sample players, exactly 8 of them
  captains):
  `in-game-name;twitch/yt_name;peak-rank;preferred-roles;platform;captain`
  - `in-game-name` and `twitch/yt_name` are both **mandatory** as of v0.34 — a row missing either
    one fails to load. The Twitch/YouTube name is shown as-is everywhere in the app (no `twitch.tv/`
    formatting) as the player's main identifier, with their in-game name shown underneath (or beside
    it, on compact rows) as a smaller subheading — put whatever handle, Twitch, YouTube, or
    otherwise, you want displayed front-and-center
  - `preferred-roles` is comma-separated, 1–3 of `Vanguard`, `Duelist`, `Strategist`
  - `peak-rank` is e.g. `Platinum 2`, or `Eternity` / `One Above All` (no subdivision)
  - `platform` is `PlayStation`, `Xbox` or `PC` (blank = no icon)
  - `captain` is `true`/`false` and must stay the **last** column - the number of `true` rows is
    your team count
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

A search box above the roster narrows it to names matching what's typed — it matches a plain
substring or the typed letters in order (e.g. "jsm" matches "JohnSmith") against **either** the
player's Twitch/YouTube name or their in-game name, and combines with the rank filter above. Each
drafted slot shows that player's preferred-role icon(s) alongside their platform icon.

## Mystery Hero

Fully-sorted teams are listed in the left "Sorted" pane; teams still waiting are in the right
"Upcoming" pane, each showing per-player assigned roles/characters (or preferred roles before
they've spun) and the captain's name, so you can track tournament-wide progress without leaving the
spin screen. **Click any team in "Upcoming" to spin for it** - the center panel switches to that
team immediately. If you switch away from a team that's partway through its role/character spins,
that team's progress is wiped and it goes back to waiting in "Upcoming", so switching mid-series is
a deliberate restart, not a pause. Once every team is fully sorted, the center panel shows a plain
"Done" message. **Back** returns to Select Tournament Type, resetting every team's spin progress
(re-picking Mystery Hero from there starts the spins over anyway).

## Bracket Settings

**Back** returns wherever this screen was reached from: Mystery Hero if you went through Role/
Character Spin, or Select Tournament Type if you picked Normal and skipped straight here.

## Bracket

Only a team's actual starting position is shown up front; a later round's
match only appears once a team has actually reached it. **Single-click** a team's name for a quick
popup with their captain's name — it closes on its own after a moment, or immediately if you click
anywhere else; **double-click** an undecided match to mark that team the winner
(it advances automatically, and in double elimination drops the loser into the losers bracket), and
double-click a decided match's winner again to undo it (an auto-resolved bye can't be undone). The
league stage's round-robin match list updates in place as results come in, so marking a winner never
resets its scroll position.

Zoom in/out with the **−/+** buttons just above the footer (bottom-center) - continuous, not fixed
steps. There's no auto-fit or scrolling: if a large bracket runs past the edge of the window, zoom
out manually to bring the rest into view.

## Congratulations

Shows the winning team's name, captain, and roster (with each player's assigned role/character, or
their preferred roles if they weren't individually assigned one). Only each player's Twitch/YouTube
name is shown here (no in-game-name subheading, unlike the other screens).
