"""Small helpers that draw a player's name, platform badge and role icons, with a text fallback if the icon files are missing."""

import tkinter as tk
from pathlib import Path

from app.data.icons import ICON_FILENAMES as ROLE_ICON_FILENAMES
from app.data.icons import get_role_glyph
from app.data.platforms import FALLBACK_TEXT, ICON_FILENAMES
from app.ui import theme

ICONS_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"
_photo_cache = {}   # also keeps PhotoImage objects alive


def _load_photo(path: Path, size: int):
    """Loads an icon file at the given size (cached). Gives back None if the file or Pillow isn't there."""
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


def platform_badge(parent, platform: str, bg: str, size: int = 18):
    """Makes a small label with the platform icon (or text if there's no icon). Gives None if there's no platform."""
    if not platform:
        return None
    px = theme.S(size)
    photo = _load_photo(ICONS_DIR / ICON_FILENAMES[platform], px)
    if photo is not None:
        return tk.Label(parent, image=photo, bg=bg, bd=0)
    return tk.Label(parent, text=FALLBACK_TEXT[platform], bg=bg, bd=0,
                     fg=theme.PLATFORM_COLOR.get(platform, theme.DIM),
                     font=theme.font(theme.SEMIBOLD, 8))


def name_with_platform(parent, player, bg: str, name_font=None, sub_font=None,
                         name_fg=None, platform_size: int = 18, show_sub: bool = True,
                         show_roles: bool = False, role_size: int = 14):
    """Makes the player's Twitch/YouTube name with their platform badge, plus their in-game name underneath unless show_sub is False."""
    col = tk.Frame(parent, bg=bg)
    top = tk.Frame(col, bg=bg)
    top.pack(anchor="w")
    tk.Label(top, text=player.twitch or player.ign, bg=bg, fg=name_fg or theme.TEXT,
              font=name_font or theme.FONT_NAME).pack(side="left")
    badge = platform_badge(top, player.platform, bg, platform_size)
    if badge is not None:
        badge.pack(side="left", padx=(6, 0))
    if show_roles:
        role_icons(top, player, bg, size=role_size).pack(side="left", padx=(6, 0))
    if show_sub:
        tk.Label(col, text=player.ign, bg=bg, fg=theme.DIM,
                  font=sub_font or theme.FONT_SMALL).pack(anchor="w")
    return col


def role_badge(parent, role: str, bg: str, size: int = 16):
    """Makes a small label with the role's icon (or a glyph if there's no icon). Gives None if there's no role."""
    if not role:
        return None
    px = theme.S(size)
    filename = ROLE_ICON_FILENAMES.get(role)
    photo = _load_photo(ICONS_DIR / filename, px) if filename else None
    if photo is not None:
        return tk.Label(parent, image=photo, bg=bg, bd=0)
    return tk.Label(parent, text=get_role_glyph(role), fg=theme.ROLE_COLOR.get(role, theme.DIM),
                     bg=bg, font=theme.font(theme.SANS, max(8, size - 5)))


def role_icons(parent, player, bg: str, size: int = 14):
    """Makes a row holding the icons for the player's preferred roles."""
    row = tk.Frame(parent, bg=bg)
    for role in player.preferred_roles:
        badge = role_badge(row, role, bg, size=size)
        if badge is not None:
            badge.pack(side="left", padx=1)
    return row
