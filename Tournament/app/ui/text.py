"""Reads assets/app_config.txt and hands out every piece of on-screen wording, falling back to built-in text when a line is missing."""

import re
from pathlib import Path

CONFIG_TXT = Path(__file__).resolve().parents[2] / "assets" / "app_config.txt"

_CONFIG_LINE = re.compile(r"^([^:=#]+?)\s*[:=]\s*(.*)$")
_BRACES = re.compile(r"\{(\w+)\}")

# Every line of wording in the app, written the way it appears in app_config.txt.
DEFAULTS = {
    "Title": "Community Rivals Tournament",
    "Host": "Unknown Host",
    "Hosted By": "Hosted by",
    "Footer": "Open-source software ({license}) — v{version}",
    "Credit": "Made by Mrit",

    "Button Start": "Start", "Button Continue": "Continue", "Button End": "End",
    "Button Back": "Back", "Button Save": "Save", "Button Reset": "Reset",
    "Button Theme": "Theme", "Button OK": "OK", "Button Cancel": "Cancel",
    "Button Confirm": "Confirm", "Button Apply": "Apply", "Button Home": "Home",

    "Tip Light Mode": "Switch to light mode", "Tip Dark Mode": "Switch to dark mode",
    "Tip Mute": "Mute", "Tip Unmute": "Unmute", "Tip Volume Down": "Volume down",
    "Tip Volume Up": "Volume up", "Tip Full Screen": "Full screen",
    "Tip Exit Full Screen": "Exit full screen",

    "Reset Popup Title": "Reset all data?",
    "Reset Popup Text": "This will reset all data. There is no way of getting it back.",
    "Unsaved Popup Title": "Unsaved changes",
    "Unsaved Popup Text": ("Unsaved changes will be lost. This will close the app and reset all data "
                           "from this tournament. There is no way of getting it back."),
    "Home Popup Text": ("Unsaved changes will be lost. This will take you back to the start and reset all data "
                        "from this tournament. There is no way of getting it back."),
    "Saved Popup Title": "Saved", "Saved Popup Text": "Your work is saved.",

    "Greeting Players": "{players} players", "Greeting Captains": "{captains} captains",
    "Greeting Teams": "{teams} teams",

    "Drafting Heading": "Drafting", "Drafting Teams Label": "Teams",
    "Drafting Roster Label": "Player roster · highest rank first",
    "Drafting Search Hint": "Search by player name", "Drafting Undrafted": "{n} undrafted",
    "Drafting Captain Tag": "Captain", "Drafting Empty Slot": "Empty slot",
    "Drafting Lock Button": "Lock Seed",
    "Drafting Select Hint": "Select a slot on the left to filter and draft.",
    "Drafting Note": "Drafting for {team} \u2014 slot {slot} ({req})",
    "Drafting Any Rank": "any rank", "Drafting Tier Only": "{tier} players only",
    "Drafting No Match": "(no matching players)",
    "Drafting Not Full": "Not all slots filled ({teams}). Click Lock Seed again to proceed anyway.",

    "Tournament Type Heading": "Select tournament type",
    "Mystery Hero Name": "Mystery Hero",
    "Mystery Hero Description": "Every player spins for a role, then a character.",
    "Normal Name": "Normal",
    "Normal Description": "Skip the spins and go straight to bracket settings.",
    "Choose": "Choose",
    "Mystery Hero Chip": "Role spin + Character spin", "Normal Chip": "No spins",

    "Mystery Hero Heading": "Mystery Hero", "Role Spin Heading": "Role Spin",
    "Character Spin Heading": "Character Spin",
    "Sorted Label": "Sorted · {done} of {teams}",
    "Upcoming Label": "Upcoming · click a team to spin for it",
    "Spin Button": "Spin", "Proceed Button": "Proceed to Bracket",
    "Player Progress": "Player {n} of {total}", "In Game": "In-game: {ign}", "Peak": "Peak: {rank}",
    "Prefers": "Prefers", "Role Label": "Role", "Captain Of": "Captain: {name}",
    "Press Spin": "Press Spin", "No Options": "No options left",
    "Characters Left": "{n} {role} characters left",
    "All Done Heading": "All teams complete", "All Done Text": "Every player has a role and a character assigned.",
    "Done Label": "Done", "Sorted Empty": "Teams show up here once every player has a role and a character.",
    "Spin Not Confirmed": "Not everyone is confirmed. Click Proceed again to continue anyway.",

    "Bracket Settings Heading": "Bracket Settings",
    "Seed Order Label": "Seed order · drag to reorder (top = seed 1)",
    "Bracket Type Label": "Bracket type",
    "Single Elimination Name": "Single Elimination",
    "Single Elimination Hint": "{teams} teams, bracket size {size} ({byes} byes). One loss eliminates a team.",
    "Double Elimination Name": "Double Elimination",
    "Double Elimination Hint": "{teams} teams, bracket size {size} ({byes} byes). A team is eliminated on their second loss.",
    "League Name": "League + Playoffs",
    "League Hint": ("{teams} teams play a full round robin ({matches} matches), "
                    "then the top 4 advance to a single-elimination playoff."),

    "Tip Move Up": "Move up", "Tip Move Down": "Move down", "Captain Line": "Captain: {name}",
    "Need Two Teams": "Need at least 2 teams to start.",

    "Bracket Heading": "Bracket — {type}",
    "Bracket Hint": "Click a team for details. Double-click to mark them the winner or undo it.",
    "Champion Label": "Champion", "End Tournament Button": "End Tournament",
    "Generate Playoffs Button": "Generate Playoffs",
    "Matches Decided": "{done} of {total} matches decided", "Champion Line": "Champion: {name}",
    "Round Robin Label": "Round robin matches", "Standings Label": "Standings",
    "Round Robin Remaining": "Round robin: {n} match(es) remaining",
    "Advance Line": "Top {n} advance to playoffs",
    "Unlocks Hint": "Unlocks once all {n} matches are decided.",
    "Winners Bracket Label": "Winners Bracket", "Losers Bracket Label": "Losers Bracket",
    "Playoffs Label": "Playoffs", "Grand Final Label": "Grand Final", "Round Label": "Round {n}",
    "Slot TBD": "TBD", "Slot Bye": "BYE", "Bye Tag": "bye",
    "Tip Zoom Out": "Zoom out", "Tip Zoom In": "Zoom in",

    "Congratulations Heading": "Congratulations!", "Winner Line": "{team} wins the tournament!",
    "No Champion Text": "The tournament hasn't crowned a champion yet.",
    "Captain Tag": "Captain", "Prefers Line": "{roles}",

    "Step Draft": "Draft", "Step Type": "Type", "Step Spin": "Spin",
    "Step Seed": "Seed", "Step Bracket": "Bracket", "Step Crown": "Crown",

    "Start Mode": "dark", "Sparkles": "off", "Grain": "on",
}

_cache = {"stamp": None, "values": {}}


def config_lines():
    """Reads app_config.txt and gives back its lines. Copes with the odd ways
    Notepad can save a file (with a BOM, or as UTF-16) so nothing silently breaks."""
    if not CONFIG_TXT.exists():
        return []
    try:
        raw = CONFIG_TXT.read_bytes()
    except OSError:
        return []
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16", errors="replace")
    else:
        text = raw.decode("utf-8-sig", errors="replace")
    return [ln.strip() for ln in text.splitlines()]


def _values():
    """Gives back every 'Key: value' line of the config file (lower-case keys, first one wins),
    re-reading the file only when it has changed on disk."""
    try:
        stamp = CONFIG_TXT.stat().st_mtime_ns
    except OSError:
        stamp = None
    if stamp != _cache["stamp"] or stamp is None:
        found = {}
        for line in config_lines():
            if not line or line.startswith("#"):
                continue
            m = _CONFIG_LINE.match(line)
            if m:
                value = m.group(2).strip().strip("\"'").strip()
                found.setdefault(m.group(1).strip().lower(), value or None)
        _cache["stamp"] = stamp
        _cache["values"] = found
    return _cache["values"]


def read_config_value(*keys):
    """Finds the first line in app_config.txt that looks like 'Key: value' (or
    'Key = value') for any of the given key names, ignoring upper/lower case,
    extra spaces and commented-out lines. Gives back the value, or None."""
    values = _values()
    for key in keys:
        value = values.get(key.lower())
        if value:
            return value
    return None


def _fill(template, values):
    """Swaps {name} placeholders for their values and leaves any other braces alone."""
    return _BRACES.sub(lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), template)


def t(key, **values):
    """Gives back the wording for a key: the app_config.txt line if there is one, otherwise the built-in text."""
    text = read_config_value(key) or DEFAULTS.get(key, key)
    return _fill(text, values)


def flag(key, default=True):
    """Reads an on/off setting (on, true, yes, 1 count as on) from the config file."""
    value = read_config_value(key)
    if value is None:
        value = DEFAULTS.get(key)
    if value is None:
        return default
    return value.strip().lower() in ("on", "true", "yes", "1")
