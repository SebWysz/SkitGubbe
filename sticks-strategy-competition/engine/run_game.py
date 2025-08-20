from __future__ import annotations
from pathlib import Path
from .loader import load_strategies
from .part1 import Part1Engine
from .part2 import Part2Engine
from .state import GameConfig
from .file_stats import record_game as record_game_file
from .singlestore_repo import get_repo as get_ss_repo


def run_single_game(strat_wrappers, goat_index=0, config: GameConfig | None = None):
    if config is None:
        config = GameConfig()
    p1 = Part1Engine(
        strat_wrappers,
        goat_index,
        time_limit_ms=config.time_limit_ms,
        random_seed=config.random_seed,
        replay_enabled=config.enable_replay,
        max_replay_events=config.max_replay_events,
    )
    collected, last_trick_winner, trump_card, wars = p1.run()
    trump = trump_card.suit if trump_card else None
    leader = last_trick_winner if last_trick_winner is not None else goat_index
    p2 = Part2Engine(
        strat_wrappers,
        collected,
        leader,
        trump,
        time_limit_ms=config.time_limit_ms,
        random_seed=config.random_seed,
        replay_enabled=config.enable_replay,
        max_replay_events=config.max_replay_events,
    )
    loser, order_out, kills, eats = p2.run()
    result = {
        "loser": strat_wrappers[loser].name,
        "trump": trump.name if trump else None,
        "wars": wars,
        "kills": kills,
        "eats": eats,
        "order_out": [strat_wrappers[i].name for i in order_out],
    }
    if config.enable_replay:
        result["replay_part1"] = p1.replay
        result["replay_part2"] = p2.replay
    # Record stats (SingleStore preferred if configured)
    try:
        repo = get_ss_repo()
    except Exception:
        repo = None
    if repo:
        try:
            repo.record_game(result, seed=config.random_seed, goat_index=goat_index)
        except Exception:
            # Fallback to file if DB write fails
            try:
                record_game_file(result)
            except Exception:
                pass
    else:
        try:
            record_game_file(result)
        except Exception:
            pass
    return result


def main():  # pragma: no cover
    strategies_dir = Path(__file__).parent.parent / "strategies"
    wrappers = load_strategies(strategies_dir)
    assert len(wrappers) >= 3, "Need at least 3 strategies"
    res = run_single_game(wrappers, goat_index=0)
    print(res)


if __name__ == "__main__":  # pragma: no cover
    main()
