from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class Part1PlayType(Enum):
    PLAY_HAND_CARD = auto()
    PLAY_DECK_TOP = auto()


@dataclass
class Part1PlayAction:
    type: Part1PlayType
    card_index: Optional[int] = None  # required for PLAY_HAND_CARD


@dataclass
class Part1SloughAction:
    card_indices: List[int]  # indices relative to current hand snapshot


class Part2ActionType(Enum):
    PLAY_RUN = auto()
    EAT = auto()


@dataclass
class Part2Action:
    type: Part2ActionType
    run_card_indices: List[int] | None = None  # indices into current hand snapshot
