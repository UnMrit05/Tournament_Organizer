"""A slot-machine style reel: names scroll down through three rows and land on the result in the middle."""

import random
import tkinter as tk

from app.ui import theme

TICK_START_MS = 50
TICK_END_MS = 190
FILLER_TICKS = 14


class SlotReel(tk.Frame):
    """A three-row spinning reel that stops on a chosen value."""

    def __init__(self, parent, width=26):
        """Builds the top, middle (result) and bottom rows."""
        super().__init__(parent, bg=theme.BG)
        self._sequence = []
        self._index = 0
        self._after_id = None
        self._on_done = None

        self.top_lbl = tk.Label(self, text="", fg=theme.DIM, bg=theme.PANEL,
                                  font=theme.FONT_BODY, width=width, height=1)
        self.top_lbl.pack(pady=(0, theme.S(2)))

        self.mid_lbl = tk.Label(self, text="\u2014", fg=theme.GOLD, bg=theme.PANEL_2,
                                  font=theme.font(theme.SEMIBOLD, 19), width=width, height=2,
                                  highlightbackground=theme.GOLD, highlightthickness=theme.S(2))
        self.mid_lbl.pack(pady=theme.S(2))

        self.bottom_lbl = tk.Label(self, text="", fg=theme.DIM, bg=theme.PANEL,
                                     font=theme.FONT_BODY, width=width, height=1)
        self.bottom_lbl.pack(pady=(theme.S(2), 0))

    def set_static(self, text):
        """Stops any spin and just shows the given text in the middle row."""
        self._cancel()
        self.top_lbl.configure(text="")
        self.bottom_lbl.configure(text="")
        self.mid_lbl.configure(text=text)

    def spin(self, options, final_value, on_done=None):
        """Spins through random picks from the options and lands on the final value, then calls on_done."""
        self._cancel()
        if not options or final_value is None:
            self.set_static(final_value or "No options left")
            if on_done:
                on_done()
            return
        filler = [random.choice(options) for _ in range(FILLER_TICKS)]
        self._sequence = filler + [final_value]
        self._index = 0
        self._on_done = on_done
        self._render_frame()
        self._schedule_next()

    def _cancel(self):
        """Stops the spin timer if one's running."""
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _frame_values(self, i):
        """Works out what goes in the top, middle and bottom rows for a given step."""
        def get(idx):
            """Grabs the value at a spot in the sequence, or blank if it's off the ends."""
            return self._sequence[idx] if 0 <= idx < len(self._sequence) else ""
        return get(i), get(i - 1), get(i - 2)

    def _render_frame(self):
        """Draws the current step onto the three rows."""
        top, mid, bottom = self._frame_values(self._index)
        self.top_lbl.configure(text=top)
        self.mid_lbl.configure(text=mid or "\u2014")
        self.bottom_lbl.configure(text=bottom)

    def _schedule_next(self):
        """Queues the next step (slowing down as it goes) or finishes up if we're at the end."""
        total = len(self._sequence)
        if self._index >= total:
            self._after_id = None
            if self._on_done:
                self._on_done()
            return
        progress = self._index / total
        delay = int(TICK_START_MS + (TICK_END_MS - TICK_START_MS) * (progress ** 2))
        self._after_id = self.after(delay, self._advance)

    def _advance(self):
        """Moves the reel on by one step."""
        self._index += 1
        self._render_frame()
        self._schedule_next()
