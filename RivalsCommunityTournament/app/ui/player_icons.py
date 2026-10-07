"""Small icon widgets for player rows: a name+platform group, and role
glyphs shown separately (e.g. on the other side of a row).

Platform icons come from assets/icons/platform_*.ico (via Pillow). If
the file or Pillow is missing, a short colored text badge (PS/XB/PC)
is shown instead, so nothing ever fails on a missing icon.
"""

import tkinter as tk
from pathlib import Path

from app.data.icons import get_role_glyph
from app.data.platforms import FALLBACK_TEXT, ICON_FILENAMES
from app.ui import theme

ICONS_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"
_photo_cache = {}   # also keeps PhotoImage objects alive


def _load_photo(path: Path, size: int):
    key = (str(path), size)
    if key in _photo_cache:
        return _photo_cache[key]
    photo = None
    if path.exists():
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception:
            photo = None
    _photo_cache[key] = photo
    return photo


def platform_badge(parent, platform: str, bg: str, size: int = 16):
    """A Label showing the platform icon (or text fallback); None if the
    player has no platform set."""
    if not platform:
        return None
    photo = _load_photo(ICONS_DIR / ICON_FILENAMES[platform], size)
    if photo is not None:
        return tk.Label(parent, image=photo, bg=bg, bd=0)
    return tk.Label(parent, text=FALLBACK_TEXT[platform], bg=bg, bd=0,
                     fg=theme.PLATFORM_COLOR.get(platform, theme.DIM),
                     font=theme.font(theme.SEMIBOLD, 7))


def name_with_platform(parent, player, bg: str, name_font=None, platform_size: int = 14):
    """A Frame with the player's name, then their platform badge right
    next to it (used on the roster list, slots, etc.)."""
    row = tk.Frame(parent, bg=bg)
    tk.Label(row, text=player.ign, bg=bg, fg=theme.TEXT,
              font=name_font or theme.FONT_NAME).pack(side="left")
    badge = platform_badge(row, player.platform, bg, platform_size)
    if badge is not None:
        badge.pack(side="left", padx=(6, 0))
    return row


def role_icons(parent, player, bg: str, size: int = 11):
    """A Frame with the player's preferred-role glyphs, colored by role."""
    row = tk.Frame(parent, bg=bg)
    for role in player.preferred_roles:
        tk.Label(row, text=get_role_glyph(role), fg=theme.ROLE_COLOR.get(role, theme.DIM),
                  bg=bg, font=theme.font(theme.SANS, size)).pack(side="left", padx=1)
    return row
