from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .cards import Card, Suit


# --- Exceptions (public for strategies to optionally catch introspect) --- #

class EngineError(Exception):
    """Base engine error."""


class TimeoutEngineError(EngineError):
    pass


class StrategyExecutionError(EngineError):
    pass


class IllegalActionError(EngineError):
    pass


@dataclass
class TrickPlay:
    player_index: int
    card: Card
    sequence: float  # order; sloughs can use fractional values


@dataclass
class Part1StateView:
    hand: List[Card]
    deck_remaining: int
    current_trick_plays: List[TrickPlay]
    have_played_this_trick: bool
    allowed_slough_indices: List[int]
    players_card_counts: List[int]
    collected_counts: List[int]
    war_active: bool
    memory: Dict[str, Any]


@dataclass
class Part2StateView:
    hand: List[Card]
    trump: Suit
    table_plays: List[dict]  # list of {player_index, cards}
    player_out: List[bool]
    player_hand_counts: List[int]
    memory: Dict[str, Any]


@dataclass
class GameConfig:
    time_limit_ms: int = 50
    max_memory_bytes: int = 1_000_000_000
    random_seed: int | None = None  # if set, applied to part1 shuffle & global randomness for this game
    min_players: int = 3
    enable_replay: bool = True
    # optional cap on stored events to prevent unbounded memory in pathological games
    max_replay_events: int = 10000


@dataclass
class ReplayEvent:
    phase: str  # 'part1' or 'part2'
    turn: int
    player: int
    type: str
    detail: dict


@dataclass
class StrategyWrapper:
    name: str
    module_name: str
    instance: Any
    memory: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameResult:
    loser_index: int
    order_out: List[int]
    turns_part1: int
    wars_part1: int
    kills_part2: int
    eats_part2: int
