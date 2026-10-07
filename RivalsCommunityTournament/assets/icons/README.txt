Class icons for the three roles, read by app/data/icons.py:

  vanguard.ico    Vanguard
  duelist.ico     Duelist / DPS
  strategist.ico  Strategist

These are placeholder icons matching the app's palette. Replace any
file with your own artwork (keep the filename) to swap the icon.

If a file here is missing, the app automatically falls back to a
native glyph for that role instead of failing — no icon is required
for the app to run.

Platform icons (shown next to players):

  platform_playstation.ico   PlayStation
  platform_xbox.ico          Xbox
  platform_pc.ico            PC

Same rule: replace any file to swap the artwork. If one is missing, a
short text badge (PS / XB / PC) is shown instead. Icons are read with
Pillow (see requirements.txt).
