"""Background music per screen and the button click sound. Does nothing quietly if pygame or the files aren't there."""

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
    """Starts the sound system the first time it's needed and says whether it worked."""
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
    """Looks for a sound file by name, trying .ogg, .mp3 then .wav."""
    for ext in EXTENSIONS:
        path = directory / f"{stem}{ext}"
        if path.exists():
            return path
    return None


def is_available() -> bool:
    """Says whether sound can actually play right now."""
    return _ensure_init()


def set_default_volume(value_1_to_10):
    """Sets the starting volume from a 1-10 number. Bad values are ignored."""
    global _volume
    try:
        v = float(value_1_to_10)
    except (TypeError, ValueError):
        return
    _volume = max(0.0, min(1.0, v / 10.0))


def play_music_for_screen(screen_name: str):
    """Plays that screen's music on loop (stopping the old track). No file means silence; same screen again changes nothing."""
    global _current_music_key
    if not _ensure_init():
        return
    if screen_name == _current_music_key:
        return
    _current_music_key = screen_name
    path = _find(MUSIC_DIR, screen_name)
    if path is None:
        stop_music()
        return
    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(0.0 if _muted else _volume)
        pygame.mixer.music.play(loops=-1)
    except Exception:
        pass


def stop_music():
    """Stops the background music."""
    global _current_music_key
    if _ensure_init():
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
    _current_music_key = None


def _apply_volume():
    """Pushes the current volume (or 0 if muted) onto the playing music."""
    if _ensure_init():
        try:
            pygame.mixer.music.set_volume(0.0 if _muted else _volume)
        except Exception:
            pass


def set_volume(value: float):
    """Sets the volume (0.0 to 1.0) right away."""
    global _volume
    _volume = max(0.0, min(1.0, value))
    _apply_volume()


def change_volume(delta: float):
    """Nudges the volume up or down by the given amount."""
    set_volume(_volume + delta)


def get_volume() -> float:
    """Gives back the current volume."""
    return _volume


def is_muted() -> bool:
    """Says whether sound is muted."""
    return _muted


def set_muted(muted: bool):
    """Turns mute on or off."""
    global _muted
    _muted = bool(muted)
    _apply_volume()


def toggle_mute() -> bool:
    """Flips mute and gives back the new state."""
    set_muted(not _muted)
    return _muted


def play_click(event=None):
    """Plays the button click sound. Hooked up once for every button in the app."""
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
