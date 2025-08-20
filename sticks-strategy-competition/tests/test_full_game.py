from pathlib import Path
from engine.loader import load_strategies
from engine.run_game import run_single_game
from engine.state import GameConfig


def test_full_game_executes():
    strat_dir = Path('sticks-strategy-competition/strategies')
    wrappers = load_strategies(strat_dir)
    assert len(wrappers) >= 3
    res = run_single_game(wrappers, goat_index=0, config=GameConfig(time_limit_ms=100))
    assert 'loser' in res and res['loser'] in [w.name for w in wrappers]
    for key in ['trump', 'wars', 'kills', 'eats', 'order_out']:
        assert key in res
    assert isinstance(res['order_out'], list)
