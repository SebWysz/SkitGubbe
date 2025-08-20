from pathlib import Path
from engine.loader import load_strategies
from engine.tournament import run_tournament, TournamentConfig


def test_tournament_runs_and_collects_stats():
    strat_dir = Path('sticks-strategy-competition/strategies')
    wrappers = load_strategies(strat_dir)
    cfg = TournamentConfig(games=5, random_seed=99, time_limit_ms=40)
    results = run_tournament(wrappers, cfg)
    lb = results['leaderboard']
    assert lb, 'Leaderboard should not be empty'
    names = {w.name for w in wrappers}
    assert names == {r['name'] for r in lb}
    total_losses = sum(r['losses'] for r in lb)
    assert total_losses == cfg.games
    assert all(r['games'] == cfg.games for r in lb)
    for r in lb:
        assert 'loss_rate' in r and 'avg_finish_position' in r
        assert 0 <= r['loss_rate'] <= 1
