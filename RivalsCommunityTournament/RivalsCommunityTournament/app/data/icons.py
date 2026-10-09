"""Resolve role/class icons: an .ico file if present, else a native glyph.

Matches the requirement: read .ico files for class icons from the
assets/icons folder, and fall back to a native (Unicode) glyph if a
character's class icon is missing from the folder.
"""

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
    """Return the .ico Path for a role if it exists on disk, else None."""
    filename = ICON_FILENAMES.get(role)
    if not filename:
        return None
    path = icons_dir / filename
    return path if path.exists() else None


def get_role_glyph(role: str) -> str:
    """Native fallback glyph for a role."""
    return FALLBACK_GLYPHS.get(role, "?")
