from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import List


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3


RANKS_PART1 = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]  # Ace low
RANKS_PART2 = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]  # Ace high

RANK_INDEX_PART1 = {r: i for i, r in enumerate(RANKS_PART1)}  # A=0
RANK_INDEX_PART2 = {r: i for i, r in enumerate(RANKS_PART2)}  # 2=0, A=12


@dataclass(frozen=True)
class Card:
    rank: str
    suit: Suit

    def part1_value(self) -> int:
        return RANK_INDEX_PART1[self.rank]

    def part2_value(self) -> int:
        return RANK_INDEX_PART2[self.rank]

    def __str__(self):  # pragma: no cover - formatting helper
        return f"{self.rank}{self.suit.name[0]}"


def make_deck() -> List[Card]:
    return [Card(r, s) for s in Suit for r in RANKS_PART1]


def touching_run(cards: List[Card]) -> bool:
    """Return True if all cards are same suit and consecutive in part-2 ordering."""
    if not cards:
        return False
    if len({c.suit for c in cards}) != 1:
        return False
    vals = sorted(c.part2_value() for c in cards)
    return all(b - a == 1 for a, b in zip(vals, vals[1:]))
