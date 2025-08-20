Skitgubbe Strategy Competition Workspace
========================================

Primary project code lives in `sticks-strategy-competition/` (engine, strategies, tests, dashboard).

Quick Start
-----------
Clone repo & create a virtual environment (Python 3.10+ recommended), then install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r sticks-strategy-competition/requirements.txt
```

Running Tests
-------------
Pytest suite (from repo root or project dir):
```bash
cd sticks-strategy-competition
pytest -q
```
All tests green example output: `10 passed`.

Running a Single Game (Smoke Test)
----------------------------------
```bash
cd sticks-strategy-competition
python - <<'PY'
from pathlib import Path
from engine.loader import load_strategies
from engine.run_game import run_single_game
from engine.state import GameConfig
wrappers = load_strategies(Path('strategies'))
res = run_single_game(wrappers, goat_index=0, config=GameConfig(time_limit_ms=80))
print(res)
PY
```

Running a Tournament
--------------------
Script helper (`scripts/run_tournament.py`):
```bash
cd sticks-strategy-competition
python scripts/run_tournament.py --games 50 --seed 123 --time-limit-ms 60
```
List available strategies:
```bash
python scripts/run_tournament.py --list
```
Filter a subset:
```bash
python scripts/run_tournament.py --include balanced_strategy,high_risk_strategy,conservative_strategy --games 30
```
Disable goat rotation:
```bash
python scripts/run_tournament.py --no-rotate-goat --games 20
```
Enable replays (slower, richer stats):
```bash
python scripts/run_tournament.py --replay --games 10
```

Launching the Dashboard
-----------------------
The Flask dashboard shows leaderboard + recent games (file or SingleStore backed).
```bash
cd sticks-strategy-competition
export FLASK_ENV=development  # optional auto-reload
python dashboard/app.py
```
Then open: http://127.0.0.1:5000/

Optional: place a `.env` in the project root (`sticks-strategy-competition/.env`) with e.g.:
```
SINGLESTORE_URI=singlestoredb://user:password@host:3306/db
SKIT_FORCE_DB=0
```

Strategy Development
--------------------
Add new strategy modules under `sticks-strategy-competition/strategies/`. Each must define a class (any name) subclassing `BaseStrategy` and expose `Strategy = ClassName`.

Common Tasks Summary
--------------------
| Task | Command |
|------|---------|
| Install deps | `pip install -r sticks-strategy-competition/requirements.txt` |
| Run tests | `pytest -q` (inside project dir) |
| Single game | inline Python snippet above |
| Tournament | `python scripts/run_tournament.py --games 50` |
| Dashboard | `python dashboard/app.py` |

For deeper engine details see `sticks-strategy-competition/README.md`.

This project was (almost) completely vibe‑coded. Enjoy hacking strategies.
