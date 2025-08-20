from __future__ import annotations
import random
from engine.strategy_interface import BaseStrategy
from engine.actions import (
    Part1PlayAction, Part1PlayType,
    Part1SloughAction,
    Part2Action, Part2ActionType,
)


class HighRiskStrategy(BaseStrategy):
    """Aggressively draws early and spends trump to secure leads.

    Part1: Favors drawing from deck when available to fish for good cards.
    Part2: If holding any trump and can win now, plays the *highest* trump.
    Otherwise uses highest non-trump to pressure opponents.
    """

    def part1_play(self, state):
        if state.current_trick_plays:
            # MUST follow rank if present; do this before any draw attempt
            lead_rank = max(state.current_trick_plays, key=lambda tp: tp.card.part1_value()).card.rank
            matches = [i for i,c in enumerate(state.hand) if c.rank == lead_rank]
            if matches:
                pick = max(matches, key=lambda i: state.hand[i].part1_value())
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=pick)
        # Only consider drawing when no obligation to match rank
        if state.deck_remaining > 0 and random.random() < 0.55:
            return Part1PlayAction(type=Part1PlayType.PLAY_DECK_TOP)
        # fallback highest card
        highest = max(range(len(state.hand)), key=lambda i: state.hand[i].part1_value())
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=highest)

    def part1_slough(self, state):
        # Discard a random allowed card sometimes to cycle
        if state.allowed_slough_indices and random.random() < 0.4:
            return Part1SloughAction(card_indices=[state.allowed_slough_indices[0]])
        return Part1SloughAction(card_indices=[])

    def part2_move(self, state):
        trump = state.trump
        if not state.table_plays:
            # lead highest trump if any else highest card
            trumps = [i for i,c in enumerate(state.hand) if c.suit == trump]
            if trumps:
                idx = max(trumps, key=lambda i: state.hand[i].part2_value())
            else:
                idx = max(range(len(state.hand)), key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[idx])
        def play_strength(play):
            top = max(play['cards'], key=lambda c: c.part2_value())
            return (top.suit == trump, top.part2_value())
        current = play_strength(max(state.table_plays, key=play_strength))
        # gather candidates able to win
        win_trumps = []
        win_non_trumps = []
        for i, c in enumerate(state.hand):
            s = (c.suit == trump, c.part2_value())
            if s[0] and not current[0]:
                win_trumps.append(i)
            elif s[0] == current[0] and s[1] > current[1]:
                (win_trumps if s[0] else win_non_trumps).append(i)
        if win_trumps:
            idx = max(win_trumps, key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[idx])
        if win_non_trumps:
            idx = max(win_non_trumps, key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[idx])
        return Part2Action(type=Part2ActionType.EAT)


Strategy = HighRiskStrategy
