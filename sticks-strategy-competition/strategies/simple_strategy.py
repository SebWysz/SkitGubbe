from __future__ import annotations
import random
from engine.strategy_interface import BaseStrategy
from engine.actions import (
    Part1PlayAction, Part1PlayType,
    Part1SloughAction,
    Part2Action, Part2ActionType,
)

class MyStrategy(BaseStrategy):
    """Example strategy template.

    Replace decision logic with something smarter. Use self.memory to persist
    per-game info (counts, seen ranks, etc.).
    """

    def part1_play(self, state):
        # If we must match rank already led (strict rule) attempt that first.
        if state.current_trick_plays:
            leading_rank = max(state.current_trick_plays, key=lambda tp: tp.card.part1_value()).card.rank
            rank_matches = [i for i, c in enumerate(state.hand) if c.rank == leading_rank]
            if rank_matches:
                # Simple heuristic: play lowest value among required rank
                choice = min(rank_matches, key=lambda i: state.hand[i].part1_value())
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=choice)
        # Optional: sometimes draw from deck if available early
        if state.deck_remaining > 0 and random.random() < 0.2:
            return Part1PlayAction(type=Part1PlayType.PLAY_DECK_TOP)
        # Fallback: play lowest valued card
        lowest = min(range(len(state.hand)), key=lambda i: state.hand[i].part1_value())
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=lowest)

    def part1_slough(self, state):
        # Example: slough nothing (conservative). Could discard duplicates, etc.
        return Part1SloughAction(card_indices=[])

    def part2_move(self, state):
        # If table empty: lead lowest single card
        if not state.table_plays:
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[self._lowest_index(state)])
        # Try to beat current highest single/run with a single card (simplistic)
        trump = state.trump
        def play_strength(play):
            top = max(play['cards'], key=lambda c: c.part2_value())
            return (top.suit == trump, top.part2_value())
        highest_play = max(state.table_plays, key=play_strength)
        cur_strength = play_strength(highest_play)
        candidates = []
        for i, c in enumerate(state.hand):
            s = (c.suit == trump, c.part2_value())
            if s[0] and not cur_strength[0]:
                candidates.append(i)
            elif s[0] == cur_strength[0] and s[1] > cur_strength[1]:
                candidates.append(i)
        if candidates:
            # choose minimal winning card
            best = min(candidates, key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[best])
        # Otherwise eat
        return Part2Action(type=Part2ActionType.EAT)

    def _lowest_index(self, state):
        return min(range(len(state.hand)), key=lambda i: state.hand[i].part1_value())

Strategy = MyStrategy