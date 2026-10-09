"""Bracket generation and progression logic - no UI code here.

A tournament is a flat dict of Match objects, each optionally pointing at
the next match its winner (and, in double elimination, its loser) feeds
into. The Bracket screen renders matches, lets the user pick a winner
(record_winner) or take a result back (undo_winner); everything else
(advancing, byes, standings, the league's playoff stage) lives here.

Byes: when the team count isn't a power of two, some first-round games
have only one team. Each match carries `expected`, the number of teams
that will EVER reach it (2 = a real game, 1 = a bye, 0 = never played).
Only expected==1 matches are auto-decided, and only once their single
team arrives - a team is never advanced past a real game.
"""

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(eq=False)
class Match:
    id: str
    round_index: int
    bracket: str                       # "W", "L", "GF", "RR", "P"
    team_a: Optional[object] = None    # a Team, or None (TBD / bye)
    team_b: Optional[object] = None
    winner: Optional[object] = None
    label: str = ""                    # e.g. "Quarterfinal", "Round 1"
    next_match_id: Optional[str] = None
    next_slot: Optional[str] = None            # "a" | "b"
    loser_next_match_id: Optional[str] = None
    loser_next_slot: Optional[str] = None
    expected: int = 2                  # teams that will ever reach this match
    auto: bool = False                 # decided automatically (a bye)

    @property
    def is_real_game(self):
        return self.expected == 2

    @property
    def is_decided(self):
        return self.winner is not None

    def other_team(self, team):
        return self.team_b if team is self.team_a else self.team_a


@dataclass
class BracketData:
    format: str                         # "single" | "double" | "league"
    matches: Dict[str, Match] = field(default_factory=dict)
    seed_order: List = field(default_factory=list)   # teams, in seed order
    champion: Optional[object] = None
    standings_locked: bool = False      # league only
    playoff_started: bool = False       # league only


# ---------------------------------------------------------------- helpers

def next_power_of_two(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def move_item(items: list, old_index: int, new_index: int):
    """Move items[old_index] to new_index in place, shifting the others
    (the reorder used by the drag-and-drop seed list)."""
    if old_index == new_index:
        return
    items.insert(new_index, items.pop(old_index))


def _seed_order_positions(n: int) -> List[int]:
    """Standard bracket slot order (1-indexed seeds) for a power-of-two
    bracket of size n, e.g. n=8 -> [1,8,4,5,2,7,3,6] (1v8, 4v5, 2v7, 3v6)."""
    if n == 1:
        return [1]
    order = []
    for s in _seed_order_positions(n // 2):
        order.extend([s, n + 1 - s])
    return order


def _assign_expected(matches: Dict[str, Match]):
    """Work out, structurally, how many teams will ever reach each match.
    A first-round match counts its real teams; every other match counts
    one per winner-feed whose source is ever played, plus one per
    loser-feed whose source is a real (2-team) game."""
    sources = {mid: [] for mid in matches}
    for m in matches.values():
        if m.next_match_id in sources:
            sources[m.next_match_id].append((m, "winner"))
        if m.loser_next_match_id in sources:
            sources[m.loser_next_match_id].append((m, "loser"))

    memo = {}

    def expected(m):
        if m.id in memo:
            return memo[m.id]
        feeds = sources[m.id]
        if not feeds:
            n = (m.team_a is not None) + (m.team_b is not None)
        else:
            n = 0
            for src, kind in feeds:
                e = expected(src)
                n += (e >= 1) if kind == "winner" else (e == 2)
        memo[m.id] = int(n)
        return memo[m.id]

    for m in matches.values():
        m.expected = expected(m)


def _resolve_bye(match: Match, all_matches: Dict[str, Match]):
    """Auto-decide a bye match (expected == 1) once its one team is there."""
    if match.winner is not None or match.expected != 1:
        return
    team = match.team_a if match.team_a is not None else match.team_b
    if team is not None:
        match.auto = True
        record_winner(match, team, all_matches)


def record_winner(match: Match, winner, all_matches: Dict[str, Match]):
    """Set a match's winner and push winner/loser into the matches they
    feed, auto-resolving any bye that results."""
    match.winner = winner
    loser = match.other_team(winner)

    if match.next_match_id:
        nxt = all_matches[match.next_match_id]
        setattr(nxt, f"team_{match.next_slot}", winner)
        _resolve_bye(nxt, all_matches)

    if match.loser_next_match_id and loser is not None:
        nxt = all_matches[match.loser_next_match_id]
        setattr(nxt, f"team_{match.loser_next_slot}", loser)
        _resolve_bye(nxt, all_matches)


def undo_winner(match: Match, all_matches: Dict[str, Match]) -> List[Match]:
    """Take back a result, along with every later result that depended on
    it (the advanced team is pulled out of the next match, and so on).
    Returns the matches whose state changed."""
    changed: List[Match] = []
    _reset_match(match, all_matches, changed)
    return changed


def _reset_match(m: Match, all_matches: Dict[str, Match], changed: List[Match]):
    if m.winner is None:
        return
    winner = m.winner
    loser = m.other_team(winner)
    m.winner = None
    m.auto = False
    changed.append(m)
    for nid, slot, team in ((m.next_match_id, m.next_slot, winner),
                            (m.loser_next_match_id, m.loser_next_slot, loser)):
        if nid is None or team is None:
            continue
        nxt = all_matches[nid]
        _reset_match(nxt, all_matches, changed)      # undo whatever it decided first
        if getattr(nxt, f"team_{slot}") is team:
            setattr(nxt, f"team_{slot}", None)
        if nxt not in changed:
            changed.append(nxt)


# ---------------------------------------------------------------- single elimination

def _round_label(round_num: int, total_rounds: int) -> str:
    remaining = total_rounds - round_num  # 0 = final
    return {0: "Final", 1: "Semifinal", 2: "Quarterfinal"}.get(remaining, f"Round {round_num + 1}")


def build_single_elimination(teams: List, id_prefix="W", start_round=0):
    """Returns (rounds, matches_by_id). rounds[0] is round 1, seeded with
    byes (None) for any spots beyond len(teams) up to the next power of
    two. Winners-only; double elimination wires loser_next_* in itself."""
    n = len(teams)
    size = next_power_of_two(max(n, 2))
    slot_teams = [teams[s - 1] if s <= n else None for s in _seed_order_positions(size)]

    all_matches: Dict[str, Match] = {}
    total_rounds = size.bit_length() - 1

    round1 = []
    for i in range(0, size, 2):
        m = Match(id=f"{id_prefix}{start_round}-{i // 2}", round_index=start_round, bracket=id_prefix,
                    team_a=slot_teams[i], team_b=slot_teams[i + 1], label=_round_label(0, total_rounds))
        all_matches[m.id] = m
        round1.append(m)
    rounds = [round1]

    prev = round1
    for r in range(1, total_rounds):
        this_round = []
        for i in range(0, len(prev), 2):
            m = Match(id=f"{id_prefix}{start_round + r}-{i // 2}", round_index=start_round + r,
                        bracket=id_prefix, label=_round_label(r, total_rounds))
            all_matches[m.id] = m
            prev[i].next_match_id, prev[i].next_slot = m.id, "a"
            prev[i + 1].next_match_id, prev[i + 1].next_slot = m.id, "b"
            this_round.append(m)
        rounds.append(this_round)
        prev = this_round

    _assign_expected(all_matches)
    for m in round1:
        _resolve_bye(m, all_matches)
    return rounds, all_matches


def build_single_bracket(teams: List) -> BracketData:
    _, matches = build_single_elimination(teams)
    data = BracketData(format="single", matches=matches, seed_order=list(teams))
    refresh_champion(data)
    return data


# ---------------------------------------------------------------- double elimination

def build_double_bracket(teams: List) -> BracketData:
    wb_rounds, matches = build_single_elimination(teams, id_prefix="W")
    R = len(wb_rounds)

    if R == 1:
        # 2-team edge case: the lone WB loser goes straight to the grand final.
        gf = Match(id="GF", round_index=0, bracket="GF", label="Grand Final")
        matches[gf.id] = gf
        wb_rounds[0][0].next_match_id, wb_rounds[0][0].next_slot = gf.id, "a"
        wb_rounds[0][0].loser_next_match_id, wb_rounds[0][0].loser_next_slot = gf.id, "b"
        _assign_expected(matches)
        data = BracketData(format="double", matches=matches, seed_order=list(teams))
        refresh_champion(data)
        return data

    lb_round = 0

    # LB round 0 (minor): WB round-1 losers, adjacent matches paired
    r1 = wb_rounds[0]
    prev_lb = []
    for i in range(0, len(r1), 2):
        m = Match(id=f"L{lb_round}-{i // 2}", round_index=lb_round, bracket="L",
                    label=f"Losers Round {lb_round + 1}")
        matches[m.id] = m
        r1[i].loser_next_match_id, r1[i].loser_next_slot = m.id, "a"
        r1[i + 1].loser_next_match_id, r1[i + 1].loser_next_slot = m.id, "b"
        prev_lb.append(m)
    lb_round += 1

    for wb_round_idx in range(1, R):
        # major round: previous LB survivors face this WB round's fresh losers
        wb_round = wb_rounds[wb_round_idx]
        major = []
        for i, lb_match in enumerate(prev_lb):
            m = Match(id=f"L{lb_round}-{i}", round_index=lb_round, bracket="L",
                        label=f"Losers Round {lb_round + 1}")
            matches[m.id] = m
            lb_match.next_match_id, lb_match.next_slot = m.id, "a"
            wb_round[i].loser_next_match_id, wb_round[i].loser_next_slot = m.id, "b"
            major.append(m)
        lb_round += 1
        prev_lb = major

        if len(prev_lb) > 1:
            # minor round: survivors play each other, halving the field
            minor = []
            for i in range(0, len(prev_lb), 2):
                m = Match(id=f"L{lb_round}-{i // 2}", round_index=lb_round, bracket="L",
                            label=f"Losers Round {lb_round + 1}")
                matches[m.id] = m
                prev_lb[i].next_match_id, prev_lb[i].next_slot = m.id, "a"
                prev_lb[i + 1].next_match_id, prev_lb[i + 1].next_slot = m.id, "b"
                minor.append(m)
            lb_round += 1
            prev_lb = minor

    lb_final = prev_lb[0]
    gf = Match(id="GF", round_index=0, bracket="GF", label="Grand Final")
    matches[gf.id] = gf
    wb_final = wb_rounds[-1][0]
    wb_final.next_match_id, wb_final.next_slot = gf.id, "a"
    lb_final.next_match_id, lb_final.next_slot = gf.id, "b"

    _assign_expected(matches)
    data = BracketData(format="double", matches=matches, seed_order=list(teams))
    refresh_champion(data)
    return data


# ---------------------------------------------------------------- league + playoffs

def build_league(teams: List) -> BracketData:
    """Round robin: every team plays every other team once. Standings are
    tallied from wins; once every RR match is decided, start_league_playoffs()
    builds a single-elimination playoff among the top teams."""
    matches: Dict[str, Match] = {}
    for i, (a, b) in enumerate(itertools.combinations(teams, 2)):
        m = Match(id=f"RR-{i}", round_index=0, bracket="RR", team_a=a, team_b=b, label="Round Robin")
        matches[m.id] = m
    return BracketData(format="league", matches=matches, seed_order=list(teams))


def league_standings(data: BracketData) -> List[tuple]:
    """[(team, wins, played), ...] best first (wins desc, then seed order)."""
    wins = {id(t): 0 for t in data.seed_order}
    played = {id(t): 0 for t in data.seed_order}
    for m in data.matches.values():
        if m.bracket != "RR":
            continue
        played[id(m.team_a)] += 1
        played[id(m.team_b)] += 1
        if m.winner is not None:
            wins[id(m.winner)] += 1
    order_index = {id(t): i for i, t in enumerate(data.seed_order)}
    rows = [(t, wins[id(t)], played[id(t)]) for t in data.seed_order]
    rows.sort(key=lambda row: (-row[1], order_index[id(row[0])]))
    return rows


def league_round_robin_complete(data: BracketData) -> bool:
    return all(m.winner is not None for m in data.matches.values() if m.bracket == "RR")


def start_league_playoffs(data: BracketData, playoff_size: int = 4):
    """Build a single-elim playoff from the top N teams by standings."""
    standings = league_standings(data)
    qualifiers = [t for t, _, _ in standings[:min(playoff_size, len(standings))]]
    _, playoff_matches = build_single_elimination(qualifiers, id_prefix="P")
    data.matches.update(playoff_matches)
    data.playoff_started = True
    data.standings_locked = True
    refresh_champion(data)


def refresh_champion(data: BracketData):
    finals = [m for m in data.matches.values() if m.bracket == "GF"]
    if finals:
        data.champion = finals[0].winner
        return
    top_bracket = "P" if any(m.bracket == "P" for m in data.matches.values()) else "W"
    candidates = [m for m in data.matches.values() if m.bracket == top_bracket]
    if not candidates:
        data.champion = None
        return
    max_round = max(m.round_index for m in candidates)
    last = [m for m in candidates if m.round_index == max_round]
    data.champion = last[0].winner if len(last) == 1 else None


def is_tournament_complete(data: BracketData) -> bool:
    if data.format == "league" and not data.playoff_started:
        return False
    return data.champion is not None
