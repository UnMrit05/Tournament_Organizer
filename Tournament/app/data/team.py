"""A team: a captain plus 5 open slots, along with any Mystery Hero results."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.data.players import Player

ROSTER_SLOTS = 5  # non-captain slots; team size is 6 with the captain

DEFAULT_ROLE_POOL = {"Vanguard": 2, "Duelist": 2, "Strategist": 2}


@dataclass
class Team:
    """One team with its captain, its player slots and its Mystery Hero state."""
    captain: Player
    name: str
    slots: List[Optional[Player]] = field(default_factory=lambda: [None] * ROSTER_SLOTS)
    slot_min_rank: List[str] = field(default_factory=lambda: ["Any"] * ROSTER_SLOTS)

    # Mystery Hero state (independent per team)
    role_pool: Dict[str, int] = field(default_factory=lambda: dict(DEFAULT_ROLE_POOL))
    player_roles: Dict[str, str] = field(default_factory=dict)        # ign -> role
    player_characters: Dict[str, str] = field(default_factory=dict)   # ign -> character name

    def all_players(self) -> List[Player]:
        """Gives back the captain plus everyone who's been put in a slot."""
        return [self.captain] + [p for p in self.slots if p is not None]

    def is_full(self) -> bool:
        """Says whether every slot has a player in it."""
        return all(p is not None for p in self.slots)

    def assign(self, index: int, player: Player):
        """Puts a player into the given slot."""
        self.slots[index] = player

    def clear_slot(self, index: int):
        """Empties the given slot."""
        self.slots[index] = None

    def reset_mystery(self):
        """Wipes this team's Mystery Hero roles and characters so it can start fresh."""
        self.role_pool = dict(DEFAULT_ROLE_POOL)
        self.player_roles = {}
        self.player_characters = {}


def next_open_slot(teams, team_index, slot_index):
    """Works out which slot to jump to next after one is filled: same team first, then the next teams.
    Gives back (team, slot) or None if everything's full."""
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
