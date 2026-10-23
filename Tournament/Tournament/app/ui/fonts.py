"""Loads the font files in assets/fonts for this app only (Windows), so they work without installing them."""

import sys
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
_FONT_EXTS = (".otf", ".ttf")
_FR_PRIVATE = 0x10


def register_local_fonts():
    """Tells Windows about every .otf/.ttf in assets/fonts, just for this program. Does nothing on other systems."""
    if sys.platform != "win32" or not FONTS_DIR.exists():
        return 0
    try:
        import ctypes
        add_font = ctypes.windll.gdi32.AddFontResourceExW
    except Exception:
        return 0
    count = 0
    for path in sorted(FONTS_DIR.iterdir()):
        if path.suffix.lower() in _FONT_EXTS:
            try:
                count += 1 if add_font(str(path), _FR_PRIVATE, 0) else 0
            except Exception:
                pass
    return count
