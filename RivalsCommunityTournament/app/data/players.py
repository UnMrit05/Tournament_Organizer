"""Load player details from the semicolon-separated player CSV.

Column order: in-game-name;twitch-name;peak-rank;preferred-roles;platform;captain
- in-game-name, twitch-name: strings
- peak-rank: e.g. "Platinum 2", "Eternity", "One Above All"
- preferred-roles: comma-separated, 1-3 of Vanguard, Duelist, Strategist
- platform: PlayStation, Xbox or PC (blank/unknown = no icon)
- captain: boolean, always the LAST true/false flag on the row

Older 5-column files (no platform column) still load.
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
    ign: str
    twitch: str
    peak_rank: str
    preferred_roles: List[str] = field(default_factory=list)
    captain: bool = False
    platform: str = ""

    def has_role(self, role: str) -> bool:
        return role in self.preferred_roles


def load_players(csv_path: Path) -> List[Player]:
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
