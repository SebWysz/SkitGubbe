from __future__ import annotations
from abc import ABC, abstractmethod
from .state import Part1StateView, Part2StateView
from .actions import Part1PlayAction, Part1SloughAction, Part2Action


class BaseStrategy(ABC):
    """Base strategy interface for Skitgubbe (sticks).

    Persistent per-strategy memory available via self.memory (dict) and also
    passed each call via state.memory.
    """

    def __init__(self):
        self.memory: dict = {}

    # -------- Part 1 ----------
    @abstractmethod
    def part1_play(self, state: Part1StateView) -> Part1PlayAction:  # pragma: no cover - interface
        """Return a Part1PlayAction (choose hand card or deck top)."""

    @abstractmethod
    def part1_slough(self, state: Part1StateView) -> Part1SloughAction:  # pragma: no cover - interface
        """Return indices to slough now (subset of allowed_slough_indices)."""

    # -------- Part 2 ----------
    @abstractmethod
    def part2_move(self, state: Part2StateView) -> Part2Action:  # pragma: no cover - interface
        """Either play a legal run that beats the current highest or eat."""
