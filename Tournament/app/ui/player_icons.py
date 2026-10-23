"""Loads the role and platform icon pictures (scaled for this screen and cached). Gives back None when a file is missing,
so callers can draw a text fallback instead."""

from pathlib import Path

from app.data.icons import ICON_FILENAMES as ROLE_ICON_FILENAMES
from app.data.platforms import ICON_FILENAMES
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


def platform_photo(platform: str, size: int):
    """Gives back the platform's icon picture at the given size (scaled for this screen), or None if there isn't one."""
    if not platform:
        return None
    return _load_photo(ICONS_DIR / ICON_FILENAMES[platform], theme.S(size))


def role_photo(role: str, size: int):
    """Gives back the role's icon picture at the given size (scaled for this screen), or None if there's no file."""
    filename = ROLE_ICON_FILENAMES.get(role)
    return _load_photo(ICONS_DIR / filename, theme.S(size)) if filename else None
