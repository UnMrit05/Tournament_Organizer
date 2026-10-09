"""Player platforms (PlayStation, Xbox, PC) and their icon lookups.

The CSV's platform column is normalised to one of PLATFORMS. Icons are
read from assets/icons (platform_*.ico); if a file is missing, the UI
falls back to a short text badge (PS / XB / PC).
"""

PLATFORMS = ["PlayStation", "Xbox", "PC"]

_ALIASES = {
    "playstation": "PlayStation", "play station": "PlayStation", "ps": "PlayStation",
    "ps4": "PlayStation", "ps5": "PlayStation", "psn": "PlayStation",
    "xbox": "Xbox", "x-box": "Xbox", "x box": "Xbox", "xb": "Xbox",
    "xbox one": "Xbox", "xbox series x": "Xbox", "xsx": "Xbox",
    "pc": "PC", "windows": "PC", "steam": "PC", "computer": "PC",
}

ICON_FILENAMES = {
    "PlayStation": "platform_playstation.ico",
    "Xbox": "platform_xbox.ico",
    "PC": "platform_pc.ico",
}

FALLBACK_TEXT = {"PlayStation": "PS", "Xbox": "XB", "PC": "PC"}


def normalize_platform(value: str) -> str:
    """Canonical platform name, or "" if blank/unrecognised."""
    return _ALIASES.get((value or "").strip().lower(), "")
