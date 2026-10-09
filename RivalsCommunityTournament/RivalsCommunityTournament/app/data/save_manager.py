"""Save/load tournament progress to a JSON save file.

Every save captures the whole draft (team names, drafted players, slot
rank filters), any Mystery Hero roles/characters, and the bracket
settings, tagged with the stage it was made at: "Seed" (Drafting),
"Spin" (Mystery Hero) or "Bracket Setting". Continue on the Greeting
screen restores everything and jumps back to that stage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.data.team import DEFAULT_ROLE_POOL

SAVES_DIR = Path(__file__).resolve().parents[2] / "saves"
SAVE_FILENAME = "last_tournament.json"

STATUS_TO_SCREEN = {
    "Seed": "seeding",
    "Spin": "mystery_spin",
    "Bracket Setting": "bracket_settings",
}


def save_state(state: dict, status: str) -> Path:
    SAVES_DIR.mkdir(exist_ok=True)
    payload = {
        "status": status,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "state": state,
    }
    path = SAVES_DIR / SAVE_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def load_state() -> Optional[dict]:
    path = SAVES_DIR / SAVE_FILENAME
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def has_save() -> bool:
    return (SAVES_DIR / SAVE_FILENAME).exists()


def serialize_app_state(app) -> dict:
    """Snapshot everything needed to resume, from the shared app object."""
    order_source = app.bracket_order or app.teams
    return {
        "tournament_type": app.tournament_type,
        "bracket_type": app.bracket_type,
        "bracket_order": [t.captain.ign for t in order_source],
        "teams": [
            {
                "captain": t.captain.ign,
                "name": t.name,
                "slots": [p.ign if p else None for p in t.slots],
                "slot_min_rank": list(t.slot_min_rank),
                "roles": dict(t.player_roles),
                "characters": dict(t.player_characters),
            }
            for t in app.teams
        ],
    }


def restore_app_state(app, payload) -> Optional[str]:
    """Apply a loaded save payload onto the app's teams. Players are
    matched by in-game-name and teams by captain, so the players CSV
    must still contain them. Returns the save's status tag."""
    if not payload:
        return None
    state = payload.get("state", {})
    by_ign = {p.ign: p for p in app.players}
    teams_by_captain = {t.captain.ign: t for t in app.teams}

    for saved in state.get("teams", []):
        team = teams_by_captain.get(saved.get("captain"))
        if team is None:
            continue
        n = len(team.slots)
        team.name = saved.get("name", team.name)

        slots = list(saved.get("slots", []))[:n]
        slots += [None] * (n - len(slots))
        team.slots = [by_ign.get(ign) if ign else None for ign in slots]

        mins = list(saved.get("slot_min_rank", []))[:n]
        mins += ["Any"] * (n - len(mins))
        team.slot_min_rank = mins

        team.player_roles = dict(saved.get("roles", {}))
        team.player_characters = dict(saved.get("characters", {}))
        pool = dict(DEFAULT_ROLE_POOL)
        for role in team.player_roles.values():
            if pool.get(role, 0) > 0:
                pool[role] -= 1
        team.role_pool = pool

    app.tournament_type = state.get("tournament_type")
    app.bracket_type = state.get("bracket_type")
    order = [teams_by_captain[i] for i in state.get("bracket_order", []) if i in teams_by_captain]
    if order:
        listed = {id(t) for t in order}
        order += [t for t in app.teams if id(t) not in listed]
    app.bracket_order = order or None
    return payload.get("status")
