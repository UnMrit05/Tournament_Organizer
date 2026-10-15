"""A little "pop in" animation for a label: it grows a bit past its size and settles back."""

from app.ui import theme

FRAME_MS = 16
# Size as a fraction of the final point size, one entry per animation
# frame: undersized -> overshoot -> settle.
_STEPS = [0.55, 0.72, 0.9, 1.12, 1.03, 0.98, 1.0]


def pop_in(label, family, size_pt, *flags, step=0):
    """Steps the label's font size through the pop frames, quietly stopping if the label has been destroyed."""
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
