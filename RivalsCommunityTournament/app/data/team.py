"""Team model: a captain plus 5 assignable slots (6 players total).

Also carries the Mystery Hero results once they're spun: player_roles
and player_characters are keyed by player in-game-name (ign).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.data.players import Player

ROSTER_SLOTS = 5  # non-captain slots; team size is 6 with the captain

DEFAULT_ROLE_POOL = {"Vanguard": 2, "Duelist": 2, "Strategist": 2}


@dataclass
class Team:
    captain: Player
    name: str
    slots: List[Optional[Player]] = field(default_factory=lambda: [None] * ROSTER_SLOTS)
    slot_min_rank: List[str] = field(default_factory=lambda: ["Any"] * ROSTER_SLOTS)

    # Mystery Hero state (independent per team)
    role_pool: Dict[str, int] = field(default_factory=lambda: dict(DEFAULT_ROLE_POOL))
    player_roles: Dict[str, str] = field(default_factory=dict)        # ign -> role
    player_characters: Dict[str, str] = field(default_factory=dict)   # ign -> character name

    def all_players(self) -> List[Player]:
        return [self.captain] + [p for p in self.slots if p is not None]

    def is_full(self) -> bool:
        return all(p is not None for p in self.slots)

    def assign(self, index: int, player: Player):
        self.slots[index] = player

    def clear_slot(self, index: int):
        self.slots[index] = None

    def reset_mystery(self):
        self.role_pool = dict(DEFAULT_ROLE_POOL)
        self.player_roles = {}
        self.player_characters = {}


def next_open_slot(teams, team_index, slot_index):
    """Where the Drafting screen should move after (team_index, slot_index)
    is filled: another open slot on the same team first (after this slot,
    then any before it), then the first open slot of the next team(s),
    wrapping around. Returns (ti, si) or None if every slot is filled."""
    team = teams[team_index]
    n_slots = len(team.slots)
    for j in list(range(slot_index + 1, n_slots)) + list(range(0, slot_index)):
        if team.slots[j] is None:
            return (team_index, j)
    for k in range(1, len(teams)):
        ti = (team_index + k) % len(teams)
        for j, p in enumerate(teams[ti].slots):
            if p is None:
                return (ti, j)
    return None
