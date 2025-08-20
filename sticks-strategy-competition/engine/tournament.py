from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Dict, Any
from .state import GameConfig, StrategyWrapper
from .run_game import run_single_game


@dataclass
class TournamentConfig:
    games: int = 50
    random_seed: int | None = None
    time_limit_ms: int = 50
    enable_replay: bool = False
    rotate_goat: bool = True


def run_tournament(wrappers: List[StrategyWrapper], config: TournamentConfig | None = None) -> Dict[str, Any]:
    if config is None:
        config = TournamentConfig()
    n = len(wrappers)
    assert n >= 3, 'Need at least 3 strategies'
    stats = {w.name: {"games": 0, "losses": 0, "positions_sum": 0, "wars": 0, "kills": 0, "eats": 0} for w in wrappers}
    base_seed = config.random_seed
    for g in range(config.games):
        goat_index = g % n if config.rotate_goat else 0
        seed = (base_seed + g) if base_seed is not None else None
        game_conf = GameConfig(time_limit_ms=config.time_limit_ms, random_seed=seed, enable_replay=config.enable_replay)
        result = run_single_game(wrappers, goat_index=goat_index, config=game_conf)
        order_names = result['order_out'] + [result['loser']]
        for pos, name in enumerate(order_names):
            s = stats[name]
            s["games"] += 1
            s["positions_sum"] += pos
        stats[result['loser']]["losses"] += 1
        for name in stats:
            stats[name]["wars"] += result['wars'] / n
            stats[name]["kills"] += result['kills'] / n
            stats[name]["eats"] += result['eats'] / n
    leaderboard = []
    for name, s in stats.items():
        games = s['games'] or 1
        leaderboard.append({
            "name": name,
            "games": s['games'],
            "losses": s['losses'],
            "loss_rate": s['losses'] / games,
            "avg_finish_position": s['positions_sum'] / games,
            "avg_wars": s['wars'] / games,
            "avg_kills": s['kills'] / games,
            "avg_eats": s['eats'] / games,
        })
    leaderboard.sort(key=lambda r: (r['loss_rate'], r['avg_finish_position']))
    return {"leaderboard": leaderboard, "raw": stats}


__all__ = ["TournamentConfig", "run_tournament"]
