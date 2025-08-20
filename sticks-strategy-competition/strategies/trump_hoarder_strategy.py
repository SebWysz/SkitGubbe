from __future__ import annotations
import random
from engine.strategy_interface import BaseStrategy
from engine.actions import (
    Part1PlayAction, Part1PlayType,
    Part1SloughAction,
    Part2Action, Part2ActionType,
)


class TrumpHoarderStrategy(BaseStrategy):
    """Avoids spending trump unless absolutely required.

    Tracks how many trumps have appeared (rough approximation using memory counters)
    to decide when to release trump cards. In Part2 only plays trump if a non-trump
    cannot win.
    """

    def __init__(self):
        super().__init__()
        self.memory['trumps_seen'] = 0

    def part1_play(self, state):
        # Update seen trumps from current trick
        for tp in state.current_trick_plays:
            if tp.card.suit == state.memory.get('trump_suit_observed'):
                self.memory['trumps_seen'] += 1
        # follow rank if must
        if state.current_trick_plays:
            lead_rank = max(state.current_trick_plays, key=lambda tp: tp.card.part1_value()).card.rank
            matches = [i for i, c in enumerate(state.hand) if c.rank == lead_rank]
            if matches:
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=min(matches))
        # Slight preference for drawing early to maybe gain more trumps later
        if state.deck_remaining > 0 and random.random() < 0.25:
            return Part1PlayAction(type=Part1PlayType.PLAY_DECK_TOP)
        # Otherwise play lowest non-trump if we have a notion of trump already in memory
        trump = state.memory.get('trump_suit_observed')
        if trump is not None:
            non_trumps = [i for i,c in enumerate(state.hand) if c.suit != trump]
            if non_trumps:
                pick = min(non_trumps, key=lambda i: state.hand[i].part1_value())
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=pick)
        # fallback lowest
        lowest = min(range(len(state.hand)), key=lambda i: state.hand[i].part1_value())
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=lowest)

    def part1_slough(self, state):
        return Part1SloughAction(card_indices=[])

    def part2_move(self, state):
        trump = state.trump
        # Memorize trump once known
        if trump is not None and 'trump_suit_observed' not in self.memory:
            self.memory['trump_suit_observed'] = trump
        # If table empty lead lowest non-trump if possible
        if not state.table_plays:
            non_trumps = [i for i,c in enumerate(state.hand) if c.suit != trump]
            if non_trumps:
                idx = min(non_trumps, key=lambda i: state.hand[i].part2_value())
            else:
                idx = min(range(len(state.hand)), key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[idx])
        # Evaluate current highest
        def play_strength(play):
            top = max(play['cards'], key=lambda c: c.part2_value())
            return (top.suit == trump, top.part2_value())
        highest = play_strength(max(state.table_plays, key=play_strength))
        # Try to beat using non-trump first
        non_trump_candidates = []
        trump_candidates = []
        for i, c in enumerate(state.hand):
            s = (c.suit == trump, c.part2_value())
            if s[0] and not highest[0]:
                trump_candidates.append(i)
            elif s[0] == highest[0] and s[1] > highest[1]:
                (trump_candidates if s[0] else non_trump_candidates).append(i)
        if non_trump_candidates:
            best = min(non_trump_candidates, key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[best])
        if trump_candidates:
            # Use highest trump only if late (heuristic: many trumps seen) else minimal
            if self.memory.get('trumps_seen', 0) < 2:
                pick = min(trump_candidates, key=lambda i: state.hand[i].part2_value())
            else:
                pick = max(trump_candidates, key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[pick])
        return Part2Action(type=Part2ActionType.EAT)


Strategy = TrumpHoarderStrategy
