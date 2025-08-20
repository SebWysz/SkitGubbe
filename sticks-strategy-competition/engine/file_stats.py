from __future__ import annotations
import json
import os
from pathlib import Path
from threading import RLock

"""Lightweight JSON-based aggregation storage.

STATS_PATH used to be a plain relative path that included the project folder
name ("sticks-strategy-competition/data/stats/…"). When the Flask app was
started from inside the project directory (cd sticks-strategy-competition &&
python dashboard/app.py) that produced a doubled path like
sticks-strategy-competition/sticks-strategy-competition/data/... which did
not exist, so the leaderboard appeared empty. We now resolve the project root
relative to this file's location and allow an env override.
"""

def _default_stats_path() -> Path:
    # file: <root>/engine/skit/file_stats.py -> parents[2] is project root
    root = Path(__file__).resolve().parents[2]
    return root / 'data' / 'stats' / 'aggregated_stats.json'

STATS_PATH = Path(os.environ.get('SKIT_STATS_PATH', _default_stats_path()))
_lock = RLock()

def _load() -> dict:
    if STATS_PATH.exists():
        try:
            return json.loads(STATS_PATH.read_text())
        except Exception:
            return {"strategies": {}}
    return {"strategies": {}}

def _save(data: dict):
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATS_PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
    tmp.replace(STATS_PATH)

def record_game(result: dict):
    order = result['order_out'] + [result['loser']]
    wars = result.get('wars', 0); kills = result.get('kills', 0); eats = result.get('eats', 0)
    n = len(order) if order else 1
    with _lock:
        data = _load()
        strat_map = data.setdefault('strategies', {})
        for pos, name in enumerate(order):
            rec = strat_map.setdefault(name, {"games": 0, "losses": 0, "positions_sum": 0, "wars": 0.0, "kills": 0.0, "eats": 0.0})
            rec['games'] += 1
            rec['positions_sum'] += pos
            rec['wars'] += wars / n
            rec['kills'] += kills / n
            rec['eats'] += eats / n
            if pos == n - 1:
                rec['losses'] += 1
        _save(data)

def load_leaderboard() -> list[dict]:
    with _lock:
        data = _load()
    lb = []
    for name, rec in data.get('strategies', {}).items():
        games = rec.get('games', 1) or 1
        lb.append({
            'strategy': name,
            'games': rec.get('games', 0),
            'losses': rec.get('losses', 0),
            'loss_rate': rec.get('losses', 0)/games,
            'avg_finish_position': rec.get('positions_sum', 0)/games,
            'avg_wars': rec.get('wars', 0.0)/games,
            'avg_kills': rec.get('kills', 0.0)/games,
            'avg_eats': rec.get('eats', 0.0)/games,
        })
    lb.sort(key=lambda x: (x['loss_rate'], x['avg_finish_position']))
    return lb
