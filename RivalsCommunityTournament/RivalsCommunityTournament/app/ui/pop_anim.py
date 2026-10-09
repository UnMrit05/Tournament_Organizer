"""A small "pop" entrance for a header label: it grows in with a brief
overshoot past its final size, the way a toast or a game title often
does, instead of just appearing. Frame-counted (not wall-clock) like the
other small animations in this app, so it behaves the same regardless of
machine speed.
"""

from app.ui import theme

FRAME_MS = 16
# Size as a fraction of the final point size, one entry per animation
# frame: undersized -> overshoot -> settle.
_STEPS = [0.55, 0.72, 0.9, 1.12, 1.03, 0.98, 1.0]


def pop_in(label, family, size_pt, *flags, step=0):
    """Animate `label`'s font through _STEPS, ending at (family, size_pt,
    *flags) via theme.font(). Safe to call on a label that may be
    destroyed mid-animation (e.g. the user navigates away quickly)."""
    try:
        if not label.winfo_exists():
            return
    except Exception:
        return
    if step >= len(_STEPS):
        label.configure(font=theme.font(family, size_pt, *flags))
        return
    label.configure(font=theme.font(family, size_pt * _STEPS[step], *flags))
    label.after(FRAME_MS, lambda: pop_in(label, family, size_pt, *flags, step=step + 1))
