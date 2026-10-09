"""Background music (per screen) and button-click sound effects.

Built on pygame's mixer, which is the one library that gives looping
playback and a volume knob without shelling out to anything external. If
pygame isn't installed, or a given screen/sfx file isn't present, every
function here quietly does nothing - same fallback pattern as the
platform/role icons (Pillow missing -> text badge instead of failing).

Files are looked up by screen name in assets/audio/music/<screen>.<ext>
and assets/audio/sfx/click.<ext>, trying .ogg, .mp3, .wav in that order.
"""

from pathlib import Path

try:
    import pygame

    _PYGAME_OK = True
except Exception:
    pygame = None
    _PYGAME_OK = False

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
MUSIC_DIR = ASSETS_DIR / "audio" / "music"
SFX_DIR = ASSETS_DIR / "audio" / "sfx"
EXTENSIONS = (".ogg", ".mp3", ".wav")

_initialized = False
_available = False       # True once pygame.mixer.init() has actually succeeded
_muted = False
_volume = 0.6
_current_music_key = None
_click_sound = None


def _ensure_init():
    global _initialized, _available
    if _initialized:
        return _available
    _initialized = True
    if not _PYGAME_OK:
        return False
    try:
        pygame.mixer.init()
        _available = True
    except Exception:
        _available = False
    return _available


def _find(directory: Path, stem: str):
    for ext in EXTENSIONS:
        path = directory / f"{stem}{ext}"
        if path.exists():
            return path
    return None


def is_available() -> bool:
    """Whether real audio playback is possible at all right now (pygame
    present and its mixer initialized)."""
    return _ensure_init()


def play_music_for_screen(screen_name: str):
    """Loop that screen's music file, if one exists. Switching to a screen
    with no music file (or back to the same screen) just leaves whatever
    is already playing / silent alone unless the track actually changes."""
    global _current_music_key
    if not _ensure_init():
        return
    if screen_name == _current_music_key:
        return
    path = _find(MUSIC_DIR, screen_name)
    if path is None:
        pygame.mixer.music.stop()
        _current_music_key = None
        return
    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(0.0 if _muted else _volume)
        pygame.mixer.music.play(loops=-1)
        _current_music_key = screen_name
    except Exception:
        _current_music_key = None


def stop_music():
    global _current_music_key
    if _ensure_init():
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
    _current_music_key = None


def _apply_volume():
    if _ensure_init():
        try:
            pygame.mixer.music.set_volume(0.0 if _muted else _volume)
        except Exception:
            pass


def set_volume(value: float):
    """value is 0.0-1.0."""
    global _volume
    _volume = max(0.0, min(1.0, value))
    _apply_volume()


def change_volume(delta: float):
    set_volume(_volume + delta)


def get_volume() -> float:
    return _volume


def is_muted() -> bool:
    return _muted


def set_muted(muted: bool):
    global _muted
    _muted = bool(muted)
    _apply_volume()


def toggle_mute() -> bool:
    set_muted(not _muted)
    return _muted


def play_click(event=None):
    """Button interaction sound. Bound once, app-wide, via
    root.bind_class("Button", "<Button-1>", audio.play_click, add="+") -
    so no individual button has to know about sound."""
    global _click_sound
    if not _ensure_init() or _muted:
        return
    if _click_sound is None:
        path = _find(SFX_DIR, "click")
        if path is None:
            _click_sound = False
        else:
            try:
                _click_sound = pygame.mixer.Sound(str(path))
            except Exception:
                _click_sound = False
    if _click_sound:
        try:
            _click_sound.set_volume(0.0 if _muted else _volume)
            _click_sound.play()
        except Exception:
            pass
