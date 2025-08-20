from pathlib import Path
from engine.loader import load_strategies
from engine.run_game import run_single_game


def test_strategies_load_and_play_one_game():
	strategies_dir = Path(__file__).parent.parent / "strategies"
	wrappers = load_strategies(strategies_dir)
	names = {w.name for w in wrappers}
	expected = {"conservative_strategy", "trump_hoarder_strategy", "high_risk_strategy", "balanced_strategy"}
	assert expected.issubset(names)
	res = run_single_game(wrappers[:3])
	assert 'loser' in res and 'order_out' in res

