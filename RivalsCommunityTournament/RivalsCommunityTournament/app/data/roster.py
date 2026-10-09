"""Load the Marvel Rivals character roster from JSON.

Expected shape (see data/characters.json):
{
  "schemaVersion": 1, "game": "Marvel Rivals", "season": "...",
  "lastVerified": "...", "characterCount": N,
  "characters": [{"name": "...", "roles": ["Duelist"]}, ...]
}

The roster is read fresh at load time (not hardcoded) since Marvel
Rivals adds characters over time.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

@dataclass
class Character:
    name: str
    roles: List[str] = field(default_factory=list)

    def matches_role(self, role: str) -> bool:
        return role in self.roles


def load_roster(json_path: Path) -> List[Character]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        Character(name=entry["name"], roles=entry.get("roles", []))
        for entry in data.get("characters", [])
    ]


def characters_for_role(characters: List[Character], role: str) -> List[Character]:
    return [c for c in characters if c.matches_role(role)]
