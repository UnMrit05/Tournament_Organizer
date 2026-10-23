"""Rank tiers (Bronze up to One Above All) and the helpers for comparing and sorting ranks.

Comparisons only look at the tier and ignore the 1/2/3 number after it.
"""

import re

RANK_TIERS = [
    "Bronze", "Silver", "Gold", "Platinum", "Diamond",
    "Grand Master", "Celestial", "Eternity", "One Above All",
]

TIER_NUMBER = {tier: i + 1 for i, tier in enumerate(RANK_TIERS)}

_SUBDIVISION_RE = re.compile(r"\s+[123]$")


def strip_subdivision(rank_str: str) -> str:
    """Chops the 1/2/3 off the end, so "Platinum 2" becomes "Platinum" and "Eternity" stays as is."""
    return _SUBDIVISION_RE.sub("", rank_str.strip())


def tier_number(rank_str: str) -> int:
    """Turns a rank like "Platinum 2" or "Platinum" into a tier number from 1 to 9."""
    tier = strip_subdivision(rank_str)
    if tier not in TIER_NUMBER:
        raise ValueError(f"Unknown rank tier: {rank_str!r}")
    return TIER_NUMBER[tier]


def meets_minimum(player_rank: str, minimum_tier: str) -> bool:
    """Says whether the player's tier is at least the minimum tier (the 1/2/3 is ignored)."""
    return tier_number(player_rank) >= tier_number(minimum_tier)


def all_ranks():
    """Gives back every rank tier from lowest to highest, without the 1/2/3."""
    return list(RANK_TIERS)


_TRAILING_SUB_RE = re.compile(r"\s+([123])$")


def rank_sort_key(rank_str: str):
    """Sort key that puts higher ranks first, with a 1 counting as better than a 3 inside the same tier."""
    tier = strip_subdivision(rank_str)
    match = _TRAILING_SUB_RE.search(rank_str.strip())
    sub = int(match.group(1)) if match else 0
    return (-TIER_NUMBER.get(tier, 0), sub)


def matches_tier(player_rank: str, tier: str) -> bool:
    """Says whether the player is in exactly this tier (so Gold only matches Gold, not Platinum)."""
    return strip_subdivision(player_rank) == tier
