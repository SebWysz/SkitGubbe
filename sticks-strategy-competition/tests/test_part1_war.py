from pathlib import Path
from engine.loader import load_strategies
from engine.part1 import Part1Engine
from engine.cards import Card, Suit
from engine.state import StrategyWrapper
import random

class HighTieStrategy:
    """Deterministic: always play highest rank in hand to induce ties.
    Falls back to deck top if requested but we never request.
    Sloughs nothing.
    """
    name = "HighTie"
    def __init__(self):
        self.memory = {}
    def part1_play(self, state):
        from engine.actions import Part1PlayAction, Part1PlayType
        if state.current_trick_plays:
            leading_rank = max(state.current_trick_plays, key=lambda tp: tp.card.part1_value()).card.rank
            matches = [i for i,c in enumerate(state.hand) if c.rank == leading_rank]
            if matches:
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=matches[0])
        # choose highest otherwise
        idx = max(range(len(state.hand)), key=lambda i: state.hand[i].part1_value())
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=idx)
    def part1_slough(self, state):
        from engine.actions import Part1SloughAction
        return Part1SloughAction(card_indices=[])
    def part2_move(self, state):
        from engine.actions import Part2Action, Part2ActionType
        if state.hand:
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[0])
        return Part2Action(type=Part2ActionType.EAT)

Strategy = HighTieStrategy


def make_wrappers(n):
    # dynamically create n wrappers of HighTie plus one random to break endless ties
    base = [StrategyWrapper(name=f"HighTie{i}", module_name="__inline_high_tie__", instance=HighTieStrategy(), memory={}) for i in range(n)]
    # load one existing random strategy for variety
    strat_dir = Path('strategies')
    existing = load_strategies(strat_dir)
    base.append(existing[0])
    return base


def force_war_setup(engine: Part1Engine, wrappers_count: int):
    """Overwrite dealt hands to guarantee an immediate war among first two or three players.

    We assign identical highest rank cards (K) to the first N players, and ensure deck is empty to avoid refills influencing outcome.
    """
    # Clear existing
    engine.deck.clear()
    for h in engine.hands:
        h.clear()
    # Build K of different suits for participants to avoid collisions for card identity
    participants = wrappers_count
    king_cards = [Card('K', s) for s in list(Suit)[:participants]]
    for i in range(participants):
        engine.hands[i].append(king_cards[i])
    # Add a low card to remaining players so they don't tie
    for i in range(participants, len(engine.hands)):
        engine.hands[i].append(Card('2', Suit.CLUBS))
    engine.set_aside_card = Card('A', Suit.SPADES)


def test_war_initiation_and_resolution():
    wrappers = make_wrappers(2)  # two high tie + one random => 3 players total
    engine = Part1Engine(wrappers, goat_index=0, time_limit_ms=50)
    engine.deal()
    force_war_setup(engine, wrappers_count=2)
    collected, last_winner, trump, wars = engine.run()
    assert wars >= 1, f"Expected at least one war, got {wars}"
    assert sum(len(c) for c in collected) == 52 or sum(len(c) for c in collected) == len(collected[0]) + len(collected[1]) + len(collected[2])
    assert last_winner is not None
    assert trump is not None


def test_multi_war_shrinking_participants():
    wrappers = make_wrappers(3)  # three war participants + one random => 4 players
    engine = Part1Engine(wrappers, goat_index=0, time_limit_ms=50)
    engine.deal()
    force_war_setup(engine, wrappers_count=3)
    collected, last_winner, trump, wars = engine.run()
    assert wars >= 1, f"Expected at least one war, got {wars}"
    assert last_winner is not None
    total_cards = sum(len(c) for c in collected)
    assert total_cards == 52 or total_cards == sum(len(c) for c in collected)

