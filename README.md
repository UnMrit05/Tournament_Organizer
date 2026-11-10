# Hero Shooter Community Tournament

Windows desktop app for running a community hero-shooter tournament: draft teams from a player roster, optionally scramble roles and heroes ("Mystery Hero"), then run the bracket.

| | |
|---|---|
| **Platform** | Windows · Python 3.10+ · Tkinter |
| **Optional extras** | Pillow (icons) · pygame-ce (audio) |
| **Network** | None. |
| **Licence** | MIT (shown on the Greeting screen) |

**Contents:** [Disclaimer](#Disclaimer) · [Quick start](#quick-start) · [Screen flow](#screen-flow) · [Data files](#data-files) · [Configuration](#configuration) · [Toolbar](#toolbar) · [Pop-ups](#pop-ups) · [Audio](#audio) · [Screens in detail](#screens-in-detail) · [Folder structure](#folder-structure) 

---

## Disclaimer

I did not create, and do not own, the game or anything from it.

- The game, its name, its characters, their names, the role names (Vanguard, Duelist, Strategist)
  and the rank names are the property of their respective owners. They are referenced here only so
  the app can organise a community event around the game.
- `data/characters.json` is a plain list of character names and roles, kept so the Mystery Hero
  spin has something to draw from. It is reference data, not game content.
- The fonts, icons and music in `assets/` were made by other people and are used under their own
  licences 
- This app is **not** affiliated with, endorsed by, or connected to the game's developer or
  publisher in any way. It is an unofficial fan-made tool.

No infringement is intended. 

---

## Quick start

1. Install **Python 3.10+** from python.org. Leave **"tcl/tk and IDLE"** ticked (default). The UI is built on it, so nothing else is required.
2. Edit `data/players.csv`, `data/characters.json` and `assets/app_config.txt` (see below).
3. Double-click **`run.bat`**

| Launcher | Behaviour |
|---|---|
| `run.bat` | Installs Pillow and pygame-ce on first run, then opens the app with no leftover command window |
| `python main.py` | Run `python -m pip install -r requirements.txt` once first |
| On failure | Error popup, details saved to `saves/crash.log` |

| Optional package | Used for | Without it |
|---|---|---|
| Pillow | Flat button faces, paper grain, backgrounds, icons, effects | Flat colours and plain buttons; platform icons become text badges (PS / XB / PC) |
| pygame-ce | Background music and click sounds | App is silent. No errors, also silent if `assets/audio/` is empty |

---

## Screen flow

Greeting → Drafting → Select Tournament Type → *(Mystery Hero: Role Spin → Character Spin, or straight through for Normal)* → Bracket Settings → Bracket → Congratulations

| Screen | Purpose |
|---|---|
| Greeting | Start / Continue / Theme / End. Shows licence and version |
| Drafting | Build teams from the roster, with rank filter and search |
| Tournament Type | Choose Mystery Hero or Normal |
| Mystery Hero | Spin a role, then a character, for every player |
| Bracket Settings | Order the seeds and pick the bracket type |
| Bracket | Run the matches and mark winners |
| Congratulations | Winning team, captain and roster |

- Team and player counts are never typed in: they come from the number of captains in `data/players.csv`.
- Every screen after Greeting has a **Home** button at the bottom-left. It returns to the start screen after the unsaved-changes warning (OK to go, Cancel to stay).
- Every screen after Greeting shows a display-only six-step tracker in the header: Draft · Type · Spin · Seed · Bracket · Crown.

---

## Data files

### `data/players.csv`

Semicolon-separated, one player per row:

`in-game-name;twitch/yt_name;peak-rank;preferred-roles;platform;captain`

| Column | Required | Values |
|---|---|---|
| `in-game-name` | Yes | Any text. Shown as a smaller subheading under (or beside) the main name |
| `twitch/yt_name` | Yes | Any handle. Shown as-is as the player's main name, with no `twitch.tv/` formatting |
| `peak-rank` | Yes | e.g. `Platinum 2`, or `Eternity` / `One Above All` (no subdivision) |
| `preferred-roles` | Yes | Comma-separated, 1–3 of `Vanguard`, `Duelist`, `Strategist` |
| `platform` | No | `PlayStation`, `Xbox`, `PC`. Blank means no icon |
| `captain` | Yes | `true` / `false`. **Must stay the last column** |

- A row missing either **name** fails to load.
- **The number of `true` rows is the team count.** The app derives every team and player count from this file.
- Older 5-column files (no platform) still load, as long as both names are filled in.

### `data/characters.json`

Manually update with an newly added characters. Read fresh on every launch.

---

## Configuration

Everything is controlled through `assets/app_config.txt`. Lines starting with `#` are off: remove the `# ` to use one.

| Key | Values | Effect |
|---|---|---|
| `Title` | text | Tournament title |
| `Host` | text | Host name |
| `Theme` | hex or colour name | Starting accent for **both** modes. Overrides `Theme Dark` / `Theme Light` |
| `Theme Dark` | hex or colour name | Starting accent in dark mode (stock mint `#4FE6C4`) |
| `Theme Light` | hex or colour name | Starting accent in light mode (stock apricot `#E9B98D`) |
| `Start Mode` | `dark` / `light` | Mode on the very first launch only |
| `Grain` | `on` / `off` | Paper texture over the background (default on) |
| `Sparkles` | `on` / `off` | Old star-field and dust effect (default off) |
| `Scale` | number, e.g. `1.5` | Overrides the automatic UI scale |
| `Font` | font family | App-wide font, installed on the machine or dropped into `assets/fonts/` |
| `Font Size` | 0.5–3.0 | Scales every font on top of the automatic scaling |
| `<Screen> Heading Font` | font family | Heading font for one screen (also sets the big Greeting and Congratulations headings) |
| `<Screen> Body Font` | font family | Body font for one screen |
| `Volume` | 1–10 | Starting volume. Toolbar buttons adjust it per session |
| *Text keys* | text | Every heading, button, hint, tooltip and pop-up message, listed at the bottom of the file |

**Notes**

- `<Screen>` is Greeting, Drafting, Tournament Type, Mystery Hero, Bracket Settings, Bracket or Congratulations. It overrides `Font` on that screen only.
- The default file has an active `Theme:` line, so stock mint / apricot never show. Comment it out with `#` to restore them.
- Colours: hex with or without `#` (`#3FA7FF`) or a plain name (`blue`).
- Keys are case-insensitive; `Theme = #3FA7FF` works. Save as UTF-8 or Notepad's UTF-16 "Unicode".
- Text keys read `# Key: built-in wording`. Keep `{braces}` like `{team}` or `{n}`: the app fills them in.

**In-app and asset overrides**

| What | How |
|---|---|
| Accent colour | **Theme** button (Greeting, top-left): R/G/B fields or hex code (kept in sync), swatch preview, Apply. Changes the accent everywhere in both modes for the session |
| App / taskbar icon | `assets/icons/app.ico`. Falls back to any other `.ico` there that is not a built-in role or platform icon, then to the default |
| Background picture | `assets/backgrounds/dark.png` and/or `light.png` (`.jpg` `.jpeg` `.webp` `.bmp` also work). Scaled to fill, edges cropped. A missing file falls back to the generated background |

---

## Toolbar

Top-right on every screen, left to right. Five small identical square buttons in the current accent colour; hover for a hint.

| Button | Action |
|---|---|
| Light / Dark | Switches the whole app without losing your place or picks. Choice is remembered in `saves/prefs.json` (`Start Mode` only sets the first launch). |
| Mute / Unmute | Mutes music and click sounds |
| Volume Down / Up | Adjusts volume |
| Fullscreen | Toggles fullscreen. **Esc** also exits |

Mute and volume still work with no audio files present; only the click sound will be affected in such a scenario.

---

## Pop-ups

| Trigger | Pop-up | Result |
|---|---|---|
| **Reset** (Drafting) | "Reset all data?" | Resets only on OK |
| **Save** (Drafting, Mystery Hero, Bracket Settings) | "Saved" notice | OK to dismiss |
| **Home** (every screen but Greeting) | Unsaved-changes warning | Returns to Greeting only on OK |
| **End** (Greeting, Congratulations) or the window's close (X) button | Unsaved-changes warning | Closes only on OK |
| **End Tournament** (Bracket) | None | Moves straight to Congratulations |

---

## Audio

Optional. Needs `pygame-ce`; without it, or with no files, the app stays silent.

| Folder | File name (any of `.ogg` `.mp3` `.wav`, tried in that order) | Plays on |
|---|---|---|
| `assets/audio/music/` | `greeting` | Greeting |
| | `seeding` | Drafting |
| | `tournament_type` | Tournament Type |
| | `mystery_spin` | Mystery Hero |
| | `bracket_settings` | Bracket Settings |
| | `bracket` | Bracket |
| | `congrats` | Congratulations |
| `assets/audio/sfx/` | `click` | Every button click |

- Music loops. Changing screen, or a track looping, cuts straight to the next track.
- A screen or click with no matching file is silent.
- Keep each file's licence in that folder's `licenses/` subfolder.

---

## Screens in detail

### Drafting

**Rank filter**

- Each slot has a pick list: All ranks included. A slot matches the **exact tier**; the 1/2/3 subdivision is ignored. "Gold" shows Gold 1, 2 and 3 and hides everyone else; "Any" shows everyone.
- Once a player is drafted, that slot's selector is locked to their tier until they are undrafted.

| Tier | Bronze | Silver | Gold | Platinum | Diamond | Grand Master | Celestial | Eternity | One Above All |
|---|---|---|---|---|---|---|---|---|---|
| Sort number | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |

**Search**

- The box above the roster matches a plain substring **or** the typed letters in order (`jsm` matches `JohnSmith`).
- It checks the Twitch/YouTube name **or** the in-game name, and combines with the rank filter.
- Each drafted slot shows the player's preferred-role icon(s) and platform icon.

### Mystery Hero

- **Layout:** "Sorted" teams on the left, spin area in the centre, "Upcoming" teams on the right, so overall progress is always visible.
- **Rows:** left-aligned names, captain's **C** after the name, then the character (once picked) and a role icon, with icons in one column at the right edge. Upcoming shows preferred roles until a player has spun.
- **Spin:** click a team in "Upcoming" to spin for it. **Spin** runs a time-based reel that eases to a stop; **Confirm** locks it in. Switching away mid-series wipes that team's progress and sends it back to "Upcoming".
- **Done:** once every team is sorted, the centre shows a "Done" message.
- **Back:** returns to Tournament Type and resets all spin progress.

### Bracket Settings

- Drag seed rows to reorder (top = seed 1).
- Pick the bracket type from three cards, each with a small diagram: single elimination, double elimination, league + playoffs.
- **Back** returns to wherever you came from: Mystery Hero, or Tournament Type if you chose Normal.
- With fewer than two teams the screen says so and will not start.

### Bracket

| Action | Result |
|---|---|
| Single-click a team name | Popup with the captain's name. Closes on its own, or at once when you click elsewhere |
| Double-click an undecided match | Marks that team the winner; it advances automatically. In double elimination the loser drops to the losers bracket |
| Double-click a decided match's winner | Undoes the result (an auto-resolved bye cannot be undone) |
| **−** / **+** (above the footer) | Zoom out / in in 10% steps, 35%–250%. Manual zoom stops auto-fit |
| Drag empty canvas | Pan |
| Mouse wheel / **Shift** + wheel | Scroll vertically / horizontally |

- Only a team's actual starting position shows up front; a later match appears once a team has reached it.
- A slot still waiting for a team says "TBD". "BYE" is used only for a real bye.
- The tree fits itself to the window when it first appears and again when it grows (for example when the losers bracket appears), never zooming in past 100%.
- League stage: the round-robin match list updates in place as results come in (scroll position is kept), with the standings panel level alongside it.
- The header shows "n of m matches decided" and, once there is one, the champion.
- **End Tournament** unlocks when the tournament is complete and moves to Congratulations.

### Congratulations

- Winning team name, captain and roster in a three-column grid. Only each player's Twitch/YouTube name is shown (no in-game subheading).

| Tournament type | Line under the name | Icon on the tile |
|---|---|---|
| Mystery Hero | The character the player was given | That character's class icon |
| Normal | Blank | The player's preferred role icons |

- **Back** returns to the bracket. **End** closes the app after the unsaved-changes warning.

---

## Folder structure

```
RivalsCommunityTournament/
├── main.py                 entry point
├── run.bat                 Windows double-click launcher
├── requirements.txt        optional extras: Pillow, pygame-ce
├── CHANGELOG.md            what changed in every version
├── INTRODUCTION.md         start-here guide for new users
├── app/
│   ├── app_state.py        root window, screen navigation, shared state, toolbar
│   ├── data/
│   │   ├── ranks.py        rank tiers and sorting
│   │   ├── players.py      player CSV loader
│   │   ├── roster.py       character JSON loader
│   │   ├── team.py         Team model
│   │   ├── bracket.py      single / double elimination, league + playoffs
│   │   ├── icons.py        role icons, with text fallback
│   │   ├── platforms.py    platform names and icons
│   │   └── save_manager.py save and load progress
│   ├── screens/            one module per screen (see Screen flow)
│   └── ui/
│       ├── theme.py        palettes, accents, spacing grid, fonts
│       ├── text.py         on-screen wording, app_config.txt reader
│       ├── prefs.py        light/dark choice (saves/prefs.json)
│       ├── fonts.py        registers assets/fonts/
│       ├── gfx.py          paper background and grain, button faces, icons, sparkles
│       ├── widgets.py      buttons, panels, chips, header bars
│       ├── kit.py          canvas list tools: scrolling, badges, rank tags, pick list
│       ├── stage.py        base class for screens: background, header, grid, footer
│       ├── dialogs.py      reset / unsaved / saved pop-ups
│       ├── picker.py       accent colour picker
│       ├── player_icons.py cached role and platform icons
│       ├── slot_reel.py    reel animation (Mystery Hero)
│       ├── pop_anim.py     heading pop-in (Greeting, Congratulations)
│       ├── popup.py        captain-name popup (Bracket)
│       └── audio.py        music and click sounds (optional)
├── data/
│   ├── players.csv         EDIT: your player roster
│   └── characters.json     EDIT / REPLACE: character roster
├── assets/
│   ├── app_config.txt      EDIT: title, host, colours, fonts, volume, all on-screen text
│   ├── icons/              REPLACE: vanguard / duelist / strategist / platform .ico, app.ico (taskbar)
│   ├── fonts/              bundled fonts; add your own here
│   │   └── licenses/       font licence files
│   ├── backgrounds/        OPTIONAL: dark.png / light.png
│   └── audio/
│       ├── music/          DROP IN: one file per screen
│       │   └── licenses/   track licence files
│       └── sfx/            DROP IN: click.ogg / .mp3 / .wav
│           └── licenses/   sound-effect licence files
└── saves/                  auto-created: last save file, prefs.json, crash.log
```
---

