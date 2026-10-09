# Rivals Community Tournament

A Windows desktop app for running a community Marvel Rivals tournament:
seed teams from a player roster, optionally scramble roles & heroes
("Mystery Hero"), then run the bracket.

## Setup (Windows)

1. Install Python 3.10+ from python.org. On the install screen, leave
   **"tcl/tk and IDLE"** checked (it's checked by default) — this is
   what the app's UI is built on, and it ships with the standard
   Windows installer, so no extra packages are required to run the app.
2. Double-click `run.bat` (or run `python main.py` from this folder).

`run.bat` also installs **Pillow** and **pygame** automatically the first time (Pillow powers the
`.ico` icons, pygame powers optional background music/click sounds). If you launch with
`python main.py` instead, run `python -m pip install -r requirements.txt` once. Both are optional:
without Pillow, platform icons show as text badges (PS / XB / PC); without pygame (or with no audio
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
│       └── audio.py            background music + click sounds (pygame, optional)
├── data/
│   ├── players.csv            EDIT THIS — your player roster
│   └── characters.json        EDIT/REPLACE — Marvel Rivals character roster
├── assets/
│   ├── tournament_info.txt    EDIT THIS — title, host, and optional Scale:/Font: overrides
│   ├── icons/                 REPLACE — vanguard.ico / duelist.ico / strategist.ico
│   └── audio/
│       ├── music/              DROP IN — one file per screen (see its README.txt)
│       └── sfx/                DROP IN — click.ogg/mp3/wav (see its README.txt)
└── saves/                     auto-created; holds the last save file
```

## Screen flow

Greeting → Drafting → Select Tournament Type → (Mystery Hero: Role
Spin → Character Spin, or straight through for Normal) → Bracket
Settings → Bracket → Congratulations.

**Status of this build:**
- **Fully implemented:** Greeting, Drafting, Select Tournament Type, Mystery Hero (see CHANGELOG
  for v0.2/v0.23/v0.30 details), Bracket Settings, Bracket (single elimination, double elimination,
  and league + playoffs - see the v0.24/v0.26/v0.30 changelog entries), and Congratulations.
- Every screen scales to the screen's resolution against a plain black background. A small
  "Made by Mrit" watermark sits bottom-right on every screen.

## Toolbar (top-right, every screen)

Left to right: **Mute/Unmute**, **Volume Up**, **Volume Down**, **Fullscreen** (Escape also exits
fullscreen). All four buttons are the same size and never overlap. Mute/volume control the optional
background music and click sounds (see "Audio" below) — the buttons still work with no audio files
present, they just have nothing to mute.

## Customizing the look (Greeting screen)

- **Theme button** (top-left) opens an RGB picker that replaces the app's accent color everywhere
  (buttons, highlights, captain name labels, etc.) — pick R/G/B, preview the swatch, then Apply.
- **Font:** uncomment and edit the `Font:` line in `assets/tournament_info.txt` to use a custom font
  family that's installed on the machine running the app, in place of the default.
- The bottom of the Greeting screen states the app's license and current version.

## Audio (optional)

Drop files into `assets/audio/music/` (named after a screen, e.g. `greeting.ogg`/`.mp3`/`.wav`) for
looping background music per screen, and `assets/audio/sfx/click.*` for a button-click sound — see
the `README.txt` in each folder for the exact filenames expected. Requires the optional `pygame`
package; with it missing, or no audio files present, the app runs normally and stays silent.

## Editing the data files

- `data/players.csv` — semicolon-separated (ships with 56 sample players):
  `in-game-name;twitch-name;peak-rank;preferred-roles;platform;captain`
  - `preferred-roles` is comma-separated, 1–3 of `Vanguard`, `Duelist`, `Strategist`
  - `peak-rank` is e.g. `Platinum 2`, or `Eternity` / `One Above All` (no subdivision)
  - `platform` is `PlayStation`, `Xbox` or `PC` (blank = no icon)
  - `captain` is `true`/`false` and must stay the **last** column
  - older 5-column files (no platform) still load
- `data/characters.json` — replace with an updated roster export as
  Marvel Rivals adds characters; the app reads it fresh each launch.

## Rank filtering (Drafting)

A slot's rank filter matches the **exact tier** - the 1/2/3 subdivision is
ignored. Selecting "Gold" **hides** every player who isn't Gold (Gold 1, 2
and 3 all show); "Any" shows everyone. Once a player is drafted, that slot's
selector is locked to their tier until they are undrafted. (Tier numbers,
used for sorting: Bronze=1 … Grand Master=6, Celestial=7, Eternity=8, One
Above All=9.)

## Mystery Hero

Already-finished teams are listed on the left and teams still waiting their turn on the right, each
showing per-player assigned roles/characters (or preferred roles before they've spun) and the
captain's name, so you can track tournament-wide progress without leaving the spin screen.

## Bracket

Only a team's actual starting position is shown up front; a later round's
match only appears once a team has actually reached it. **Single-click** a team's name for a quick
popup with their captain's name; **double-click** an undecided match to mark that team the winner
(it advances automatically, and in double elimination drops the loser into the losers bracket), and
double-click a decided match's winner again to undo it (an auto-resolved bye can't be undone). The
league stage's round-robin match list updates in place as results come in, so marking a winner never
resets its scroll position.

Zoom is continuous (drag between min/max) and there's a **Fit** button to re-fit the whole bracket
to the window at any time; the view also auto-fits the moment the screen opens.
