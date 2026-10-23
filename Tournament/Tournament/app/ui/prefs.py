"""Remembers small personal choices (like light or dark mode) between sessions in saves/prefs.json."""

import json
from pathlib import Path

PREFS_PATH = Path(__file__).resolve().parents[2] / "saves" / "prefs.json"


def load():
    """Reads the saved choices, or gives back an empty dict if there's no file or it's broken."""
    try:
        with open(PREFS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(**changes):
    """Adds the given choices to the saved ones. Quietly does nothing if the file can't be written."""
    data = load()
    data.update(changes)
    try:
        PREFS_PATH.parent.mkdir(exist_ok=True)
        with open(PREFS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass
