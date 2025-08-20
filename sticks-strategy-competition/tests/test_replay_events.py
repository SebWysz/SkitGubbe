from pathlib import Path
from engine.loader import load_strategies
from engine.run_game import run_single_game
from engine.state import GameConfig


def test_replay_summaries_and_beat_reasons():
    strat_dir = Path('sticks-strategy-competition/strategies')
    wrappers = load_strategies(strat_dir)
    config = GameConfig(time_limit_ms=80, enable_replay=True, random_seed=1234)
    res = run_single_game(wrappers, goat_index=0, config=config)
    part1 = res.get('replay_part1')
    assert part1, 'Expected part1 replay events'
    assert part1[-1].type == 'summary'
    summary1 = part1[-1].detail
    assert 'wars' in summary1 and 'tricks_played' in summary1 and 'trump_card' in summary1
    part2 = res.get('replay_part2')
    assert part2, 'Expected part2 replay events'
    assert part2[-1].type == 'summary'
    summary2 = part2[-1].detail
    assert 'loser' in summary2 and 'kills' in summary2 and 'eats' in summary2
    run_events = [e for e in part2 if e.type == 'run_play']
    if run_events:
        allowed = {"first","trump_over_nontrump","cannot_over_trump","higher_value","longer_run","not_higher"}
        assert all('beat_reason' in e.detail for e in run_events)
        assert any(e.detail.get('beat_reason') in allowed for e in run_events)
