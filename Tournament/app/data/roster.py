"""Loads the list of playable characters and their roles from the characters JSON file."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

@dataclass
class Character:
    """A playable character and the roles they can fill."""
    name: str
    roles: List[str] = field(default_factory=list)

    def matches_role(self, role: str) -> bool:
        """Says whether this character can play the given role."""
        return role in self.roles


def load_roster(json_path: Path) -> List[Character]:
    """Reads the JSON file and gives back the list of characters."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        Character(name=entry["name"], roles=entry.get("roles", []))
        for entry in data.get("characters", [])
    ]


def characters_for_role(characters: List[Character], role: str) -> List[Character]:
    """Picks out just the characters who can play the given role."""
    return [c for c in characters if c.matches_role(role)]
