from __future__ import annotations
from engine.strategy_interface import BaseStrategy
from engine.actions import (
    Part1PlayAction, Part1PlayType,
    Part1SloughAction,
    Part2Action, Part2ActionType,
)


class BalancedStrategy(BaseStrategy):
    """Hybrid heuristics — aims to keep hand balanced between suits.

    Part1: Follows rank; otherwise plays a card from the most common suit in hand
    (to shed redundancy) choosing the lowest of that suit.
    Part2: Prefers to win using a non-trump mid-value card; saves extremes.
    """

    def part1_play(self, state):
        if state.current_trick_plays:
            lead_rank = max(state.current_trick_plays, key=lambda tp: tp.card.part1_value()).card.rank
            matches = [i for i,c in enumerate(state.hand) if c.rank == lead_rank]
            if matches:
                # play middle (median) among matching to avoid extremes
                matches.sort(key=lambda i: state.hand[i].part1_value())
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=matches[len(matches)//2])
        # frequency of suits
        suit_to_indices = {}
        for i,c in enumerate(state.hand):
            suit_to_indices.setdefault(c.suit, []).append(i)
        # choose suit with max count
        suit_indices = max(suit_to_indices.values(), key=len)
        pick = min(suit_indices, key=lambda i: state.hand[i].part1_value())
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=pick)

    def part1_slough(self, state):
        # Slough duplicate ranks if allowed (example heuristic)
        chosen = []
        seen = set()
        for i in state.allowed_slough_indices:
            r = state.hand[i].rank
            if r in seen:
                chosen.append(i)
                break
            seen.add(r)
        return Part1SloughAction(card_indices=chosen)

    def part2_move(self, state):
        if not state.table_plays:
            # lead median strength card to keep balance
            ordered = sorted(range(len(state.hand)), key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[ordered[len(ordered)//2]])
        trump = state.trump
        def play_strength(play):
            top = max(play['cards'], key=lambda c: c.part2_value())
            return (top.suit == trump, top.part2_value())
        highest = play_strength(max(state.table_plays, key=play_strength))
        # attempt winning using mid-strength card
        candidates = []
        for i, c in enumerate(state.hand):
            s = (c.suit == trump, c.part2_value())
            if s[0] and not highest[0]:
                candidates.append(i)
            elif s[0] == highest[0] and s[1] > highest[1]:
                candidates.append(i)
        if candidates:
            candidates.sort(key=lambda i: state.hand[i].part2_value())
            mid = candidates[len(candidates)//2]
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[mid])
        return Part2Action(type=Part2ActionType.EAT)


Strategy = BalancedStrategy
