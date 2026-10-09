"""Rivals Community Tournament — entry point.

Run with: python main.py
(or double-click run.bat on Windows)
"""

from app.app_state import TournamentApp

if __name__ == "__main__":
    app = TournamentApp()
    app.mainloop()
