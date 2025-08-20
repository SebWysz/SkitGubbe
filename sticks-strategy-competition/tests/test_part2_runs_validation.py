from pathlib import Path
import pytest
from engine.loader import load_strategies
from engine.part1 import Part1Engine
from engine.part2 import Part2Engine
from engine.state import GameConfig


def test_part2_infinite_loop_safeguard_not_triggered():
    strat_dir = Path('strategies')
    wrappers = load_strategies(strat_dir)
    p1 = Part1Engine(wrappers, goat_index=0, time_limit_ms=50)
    collected, last_winner, trump_card, wars = p1.run()
    assert trump_card is not None
    engine2 = Part2Engine(wrappers, collected, initial_leader=last_winner, trump=trump_card.suit, time_limit_ms=50)
    loser, order_out, kills, eats = engine2.run()
    assert loser in range(len(wrappers))
    assert len(order_out) <= len(wrappers)
    assert kills >= 0 and eats >= 0


def test_part2_illegal_duplicate_indices():
    # Craft a malicious strategy injecting duplicate run indices
    from engine.actions import Part2Action, Part2ActionType
    class DupStrategy:
        name = "Dup"
        def __init__(self):
            self.memory = {}
        def part1_play(self, state):
            from engine.actions import Part1PlayAction, Part1PlayType
            ranks_on_table = {tp.card.rank for tp in state.current_trick_plays}
            if ranks_on_table:
                matching = [i for i, c in enumerate(state.hand) if c.rank in ranks_on_table]
                if matching:
                    return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=matching[0])
            return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=0)
        def part1_slough(self, state):
            from engine.actions import Part1SloughAction
            return Part1SloughAction(card_indices=[])
        def part2_move(self, state):
            if state.hand:
                # intentionally duplicate first index
                return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[0,0])
            return Part2Action(type=Part2ActionType.EAT)
    from engine.state import StrategyWrapper
    wrappers = [StrategyWrapper(name='Dup', module_name='dup_mod', instance=DupStrategy()),]
    # add one normal strategy to allow game progress
    strat_dir = Path('strategies')
    wrappers.extend(load_strategies(strat_dir)[:2])
    p1 = Part1Engine(wrappers, goat_index=0, time_limit_ms=50)
    collected, last_winner, trump_card, wars = p1.run()
    assert trump_card is not None
    engine2 = Part2Engine(wrappers, collected, initial_leader=last_winner, trump=trump_card.suit, time_limit_ms=50)
    from engine.state import IllegalActionError
    with pytest.raises(IllegalActionError):
        engine2.run()

