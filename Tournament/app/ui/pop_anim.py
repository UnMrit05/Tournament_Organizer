"""A little "pop in" animation for a label: it grows a bit past its size and settles back."""

from app.ui import theme

FRAME_MS = 16
# Size as a fraction of the final point size, one entry per animation
# frame: undersized -> overshoot -> settle.
_STEPS = [0.55, 0.72, 0.9, 1.12, 1.03, 0.98, 1.0]


def pop_in(label, family, size, *flags, step=0, px=False):
    """Steps the label's font size through the pop frames, quietly stopping if the label has been destroyed.
    The size is in points, or in reference pixels when px is True."""
    try:
        if not label.winfo_exists():
            return
    except Exception:
        return
    make_font = theme.fpx if px else theme.font
    if step >= len(_STEPS):
        label.configure(font=make_font(family, size, *flags))
        return
    label.configure(font=make_font(family, size * _STEPS[step], *flags))
    label.after(FRAME_MS, lambda: pop_in(label, family, size, *flags, step=step + 1, px=px))


def pop_in_item(canvas, item, family, size, *flags, step=0):
    """Same pop-in, but for a piece of text drawn on a canvas (size in reference pixels)."""
    try:
        if not canvas.winfo_exists():
            return
    except Exception:
        return
    if step >= len(_STEPS):
        canvas.itemconfigure(item, font=theme.fpx(family, size, *flags))
        return
    canvas.itemconfigure(item, font=theme.fpx(family, size * _STEPS[step], *flags))
    canvas.after(FRAME_MS, lambda: pop_in_item(canvas, item, family, size, *flags, step=step + 1))
