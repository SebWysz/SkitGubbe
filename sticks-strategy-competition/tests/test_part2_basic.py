from pathlib import Path
from engine.loader import load_strategies
from engine.run_game import run_single_game
from engine.state import GameConfig


def test_part2_progress_metrics():
    strat_dir = Path('strategies')
    wrappers = load_strategies(strat_dir)
    assert len(wrappers) >= 3
    res = run_single_game(wrappers, goat_index=0, config=GameConfig(time_limit_ms=100))
    assert res['kills'] >= 0
    assert res['eats'] >= 0
    # Trump may be None if part1 produced no last trick winner (edge abort) but normally is a suit
    assert res['trump'] is None or res['trump'] in {'CLUBS','DIAMONDS','HEARTS','SPADES'}
