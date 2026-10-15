"""The platforms players can be on (PlayStation, Xbox, PC) and the icons/badges for them."""

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
    """Turns whatever was typed in the CSV into a proper platform name, or "" if it's blank or unknown."""
    return _ALIASES.get((value or "").strip().lower(), "")
