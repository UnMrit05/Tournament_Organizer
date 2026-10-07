"""Rank tier system for Marvel Rivals peak ranks.

v0.2: filtering compares TIERS ONLY, ignoring the 1/2/3 subdivision.
A full peak-rank string ("Platinum 2") is still stored and displayed
as-is, but for the purpose of the Seeding screen's rank filter, the
subdivision is stripped and each tier gets a plain numeric value:

    Bronze=1, Silver=2, Gold=3, Platinum=4, Diamond=5,
    Grand Master=6, Celestial=7, Eternity=8, One Above All=9

Selecting e.g. "Platinum" as a slot's minimum rank filters the roster
to players whose tier number is >= 4 (Platinum, Diamond, Grand
Master, Celestial, Eternity, One Above All) - regardless of whether
they're Platinum 3 or Platinum 1.
"""

import re

RANK_TIERS = [
    "Bronze", "Silver", "Gold", "Platinum", "Diamond",
    "Grand Master", "Celestial", "Eternity", "One Above All",
]

TIER_NUMBER = {tier: i + 1 for i, tier in enumerate(RANK_TIERS)}

_SUBDIVISION_RE = re.compile(r"\s+[123]$")


def strip_subdivision(rank_str: str) -> str:
    """"Platinum 2" -> "Platinum"; "Eternity" -> "Eternity" (unchanged)."""
    return _SUBDIVISION_RE.sub("", rank_str.strip())


def tier_number(rank_str: str) -> int:
    """Numeric tier value (1-9) for a full ("Platinum 2") or tier-only
    ("Platinum") rank string."""
    tier = strip_subdivision(rank_str)
    if tier not in TIER_NUMBER:
        raise ValueError(f"Unknown rank tier: {rank_str!r}")
    return TIER_NUMBER[tier]


def meets_minimum(player_rank: str, minimum_tier: str) -> bool:
    """True if player_rank's tier is >= minimum_tier's tier.
    Subdivision is ignored on both sides."""
    return tier_number(player_rank) >= tier_number(minimum_tier)


def all_ranks():
    """All valid rank tiers, lowest to highest (no subdivisions)."""
    return list(RANK_TIERS)


_TRAILING_SUB_RE = re.compile(r"\s+([123])$")


def rank_sort_key(rank_str: str):
    """Sort key for a full rank string so that higher ranks sort first
    (tier descending, then subdivision 1/2/3 ascending since 1 is the
    strongest subdivision within a tier)."""
    tier = strip_subdivision(rank_str)
    match = _TRAILING_SUB_RE.search(rank_str.strip())
    sub = int(match.group(1)) if match else 0
    return (-TIER_NUMBER.get(tier, 0), sub)


def matches_tier(player_rank: str, tier: str) -> bool:
    """True if the player's tier is exactly `tier` (subdivision ignored).
    Used by the Drafting screen's rank filter: picking Gold shows only
    Gold players, not Gold-and-above."""
    return strip_subdivision(player_rank) == tier
