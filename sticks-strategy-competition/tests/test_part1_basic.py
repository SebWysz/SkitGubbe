from pathlib import Path
from engine.loader import load_strategies
from engine.part1 import Part1Engine


def test_part1_runs_and_collects_cards():
    strat_dir = Path('strategies')
    wrappers = load_strategies(strat_dir)
    assert len(wrappers) >= 3
    p1 = Part1Engine(wrappers, goat_index=0, time_limit_ms=100)
    collected, last_trick_winner, trump_card, wars = p1.run()
    total = sum(len(c) for c in collected)
    # 52 cards in deck including set-aside card should now all be in collected piles
    assert total == 52
    assert trump_card is not None
    assert 0 <= wars <= 52
