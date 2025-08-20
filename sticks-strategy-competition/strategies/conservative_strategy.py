from __future__ import annotations
import random
from engine.strategy_interface import BaseStrategy
from engine.actions import (
    Part1PlayAction, Part1PlayType,
    Part1SloughAction,
    Part2Action, Part2ActionType,
)


class ConservativeStrategy(BaseStrategy):
    """Plays safest / lowest options, hoards high cards.

    Part1: Always follow rank if required; otherwise play lowest valued card.
    Rarely draws from deck (only very early).
    Part2: Attempts to win using the *lowest* winning single; otherwise eats.
    """

    def part1_play(self, state):
        # follow rank if present
        if state.current_trick_plays:
            lead_rank = max(state.current_trick_plays, key=lambda tp: tp.card.part1_value()).card.rank
            matches = [i for i, c in enumerate(state.hand) if c.rank == lead_rank]
            if matches:
                pick = min(matches, key=lambda i: state.hand[i].part1_value())
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=pick)
        # tiny chance to draw if very early and deck available
        if state.deck_remaining > 0 and sum(state.players_card_counts) > 30 and random.random() < 0.05:
            return Part1PlayAction(type=Part1PlayType.PLAY_DECK_TOP)
        # else lowest card
        lowest = min(range(len(state.hand)), key=lambda i: state.hand[i].part1_value())
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=lowest)

    def part1_slough(self, state):
        # Never slough (keeps optional flexibility)
        return Part1SloughAction(card_indices=[])

    def part2_move(self, state):
        # If table empty lead the absolute lowest card
        if not state.table_plays:
            idx = min(range(len(state.hand)), key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[idx])
        # Determine strength of current highest
        trump = state.trump
        def play_strength(play):
            top = max(play['cards'], key=lambda c: c.part2_value())
            return (top.suit == trump, top.part2_value())
        current = play_strength(max(state.table_plays, key=play_strength))
        # Find minimal winning single
        candidates = []
        for i, c in enumerate(state.hand):
            s = (c.suit == trump, c.part2_value())
            if s[0] and not current[0]:
                candidates.append(i)
            elif s[0] == current[0] and s[1] > current[1]:
                candidates.append(i)
        if candidates:
            best = min(candidates, key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[best])
        return Part2Action(type=Part2ActionType.EAT)


Strategy = ConservativeStrategy
