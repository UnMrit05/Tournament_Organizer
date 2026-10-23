"""Finds the icon for each role, using an .ico file if there is one and a plain glyph if not."""

from pathlib import Path
from typing import Optional

ICON_FILENAMES = {
    "Vanguard": "vanguard.ico",
    "Duelist": "duelist.ico",
    "Strategist": "strategist.ico",
}

# Native fallback glyphs, used only if the matching .ico is missing.
FALLBACK_GLYPHS = {
    "Vanguard": "\u26E8",   # shield
    "Duelist": "\u2694",    # crossed swords
    "Strategist": "\u271A", # heavy plus
}


def get_role_icon_path(icons_dir: Path, role: str) -> Optional[Path]:
    """Gives back the path to a role's .ico file, or None if it isn't there."""
    filename = ICON_FILENAMES.get(role)
    if not filename:
        return None
    path = icons_dir / filename
    return path if path.exists() else None


def get_role_glyph(role: str) -> str:
    """Gives back the little text symbol to use when a role has no .ico file."""
    return FALLBACK_GLYPHS.get(role, "?")
