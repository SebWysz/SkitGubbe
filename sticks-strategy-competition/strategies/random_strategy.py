from __future__ import annotations
import random
from engine.strategy_interface import BaseStrategy
from engine.actions import (
    Part1PlayAction,
    Part1PlayType,
    Part1SloughAction,
    Part2Action,
    Part2ActionType,
)


class RandomStrategy(BaseStrategy):
    """Very naive baseline strategy."""

    def part1_play(self, state):
        if state.current_trick_plays:
            leading_rank = max(state.current_trick_plays, key=lambda tp: tp.card.part1_value()).card.rank
            leading_matches = [i for i,c in enumerate(state.hand) if c.rank == leading_rank]
            if leading_matches:
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=random.choice(leading_matches))
        # Otherwise free choice / draw bias
        if state.deck_remaining > 0 and random.random() < 0.25:
            return Part1PlayAction(type=Part1PlayType.PLAY_DECK_TOP)
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=random.randrange(len(state.hand)))

    def part1_slough(self, state):
        if state.allowed_slough_indices and random.random() < 0.3:
            return Part1SloughAction(card_indices=[random.choice(state.allowed_slough_indices)])
        return Part1SloughAction(card_indices=[])

    def part2_move(self, state):
        # Attempt to find a single card that beats current highest (or any if table empty)
        table = state.table_plays
        if not table:
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[0])
        # Determine highest play top card value (approx by suit/trump and part2_value)
        trump = state.trump
        def play_strength(play):
            top = max(play['cards'], key=lambda c: c.part2_value())
            return (top.suit == trump, top.part2_value())
        current_strength = play_strength(max(table, key=play_strength))
        # scan hand for beating single
        candidates = []
        for idx, c in enumerate(state.hand):
            s = (c.suit == trump, c.part2_value())
            if s[0] and not current_strength[0]:  # any trump beats non-trump
                candidates.append(idx)
            elif s[0] == current_strength[0] and s[1] > current_strength[1]:
                candidates.append(idx)
        if candidates:
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[candidates[0]])
        return Part2Action(type=Part2ActionType.EAT)


Strategy = RandomStrategy
