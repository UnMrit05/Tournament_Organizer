"""Saves and loads tournament progress in a JSON file, tagged with the stage you were on."""

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
    """Writes the current progress and its stage tag to the save file and gives back where it went."""
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
    """Reads the save file, or gives back None if there isn't one."""
    path = SAVES_DIR / SAVE_FILENAME
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def has_save() -> bool:
    """Says whether a save file exists yet."""
    return (SAVES_DIR / SAVE_FILENAME).exists()


def serialize_app_state(app) -> dict:
    """Boils the app's teams and bracket settings down to something that can be saved."""
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
    """Puts saved progress back onto the app's teams, matching players by in-game name and teams by captain.
    Gives back the save's stage tag."""
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
