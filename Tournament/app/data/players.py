"""Reads the player list from the semicolon-separated CSV.

Columns: in-game-name;twitch/yt_name;peak-rank;preferred-roles;platform;captain
(the captain flag is always last, and files without a platform column still load).
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from app.data.platforms import normalize_platform

VALID_ROLES = {"Vanguard", "Duelist", "Strategist"}
HEADER_MARKERS = {"in-game-name", "ign", ""}


@dataclass
class Player:
    """One player's details straight from the CSV."""
    ign: str
    twitch: str
    peak_rank: str
    preferred_roles: List[str] = field(default_factory=list)
    captain: bool = False
    platform: str = ""

    def has_role(self, role: str) -> bool:
        """Says whether this player listed the given role as one they like."""
        return role in self.preferred_roles


def load_players(csv_path: Path) -> List[Player]:
    """Grabs the player list from the CSV and makes sure nobody's missing a name or has a bogus role."""
    players: List[Player] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            if not row or row[0].strip().lower() in HEADER_MARKERS:
                continue  # skip blank lines and header row
            cells = [c.strip() for c in row]
            while len(cells) < 5:
                cells.append("")
            ign, twitch, peak_rank, roles_field = cells[:4]
            captain_field = cells[-1]                       # captain is always last
            platform_field = cells[4] if len(cells) >= 6 else ""

            roles = [r.strip() for r in roles_field.split(",") if r.strip()]
            for r in roles:
                if r not in VALID_ROLES:
                    raise ValueError(f"Unknown role {r!r} for player {ign!r}")

            if not ign.strip():
                raise ValueError("Every player row needs an in-game name")
            if not twitch.strip():
                raise ValueError(f"Player {ign!r} is missing a Twitch/YouTube name - "
                                   f"it's mandatory")

            captain = captain_field.strip().lower() in ("true", "1", "yes")

            players.append(Player(
                ign=ign.strip(),
                twitch=twitch.strip(),
                peak_rank=peak_rank.strip(),
                preferred_roles=roles,
                captain=captain,
                platform=normalize_platform(platform_field),
            ))
    return players
