# Skitgubbe (Flurst) Strategy Competition

This repository hosts an engine and scaffolding for running automated strategy tournaments for the Swedish card game Skitgubbe (a.k.a. Flurst). Players submit Python strategy modules which the engine loads, sandboxes, and pits against each other. The system provides a tournament runner, replay / stats persistence (file or SingleStore), and a web dashboard.

## High-Level Flow
1. Part 1: "Match If You Can" — players attempt to match ranks; winners of tricks collect cards. Ties trigger a war among only tied players until resolved. A single card is set aside at the deal and awarded to the winner of the final completed trick (or goat seat if none).
2. Part 2: "Beat It or Eat It" — players attempt to run (lay legal touching run starting from lowest rank) or eat (draw) when they can't beat; kills and eats tracked; last player holding cards loses.

## Current Implementation
* Part 1 engine with explicit war loop over tied participants.
* Part 2 engine with run / eat sequencing, kill & eat metrics, replay events with reasoning.
* Strategy interface (`engine/strategy_interface.py`) exposing:
  - `part1_play(state)` -> choose card or deck top
  - `part1_slough(state)` -> optionally slough matching ranks already on table
  - `part2_move(state)` -> propose a run (subset of hand) or eat
* Example strategies in `strategies/`.
* Sandbox wrapper enforcing a per-decision wall-clock timeout (default 50ms).
* Pytest suite validating core invariants (`tests/`).
* Native SingleStore driver integration (`engine/singlestore_repo.py`) with file fallback.
* Dashboard (`dashboard/`) serving live leaderboard + recent games.

## War Logic (Part 1)
When multiple highest cards tie within a trick, a war starts:
* Only tied players remain active war participants.
* They continue playing required cards in rotating order among themselves.
* Additional ties shrink the participant set further.
* A unique highest card resolves the war; that player collects the entire trick stack.
Planned enhancements: support optional variants (face-down burn cards, multi-reveal) if needed.

## Sloughing (Part 1)
After each required play, a discrete slough round lets players discard (slough) additional copies of ranks already on the table (with restrictions preventing circumventing mandatory future match plays). This is a simplified discrete model approximating simultaneous announcements; may be refined.

## Strategy Development
Place strategy files inside `strategies/` with a class named `Strategy` implementing the three methods. Avoid banned imports (network, filesystem). The loader performs a basic AST scan; stricter sandboxing (resource limits, import filtering) is on the roadmap.

Minimal template:
```python
from engine.strategy_interface import BaseStrategy

class Strategy(BaseStrategy):
   name = "MyStrategy"

   def part1_play(self, state):
      # decide Part1PlayAction
      ...
   def part1_slough(self, state):
      # return Part1SloughAction or None
      return None
   def part2_move(self, state):
      # return Part2Action
      ...
```

## Running a Single Game
```bash
python - <<'PY'
from pathlib import Path
from engine.loader import load_strategies
from engine.run_game import run_single_game
from engine.state import GameConfig

wrappers = load_strategies(Path('sticks-strategy-competition/strategies'))
res = run_single_game(wrappers, goat_index=0, config=GameConfig(time_limit_ms=100))
print(res)
PY
```

## Roadmap / TODO
* Optional war variants (burn / multi-stage) & expanded tests.
* Enhanced slough modeling (simultaneous declarations).
* ELO / rating systems atop aggregated stats.
* Cross-game persistent learning hooks for strategies.
* Hardened sandbox: memory limiter, syscall filtering.
* Additional dashboard visualizations (distribution charts, per-strategy trend lines).

## Contributing
PRs welcome for engine correctness, new sample strategies, or infrastructure pieces. Please include tests for behavioral changes.

## License
MIT (see LICENSE).

## Environment Configuration (.env)
Place a `.env` file at the repository root to supply runtime settings without exporting manually. Example:

```
SINGLESTORE_URI=singlestoredb://user:ENCODED_PASSWORD@host:3333/db_name
SKIT_FORCE_DB=1  # require DB or mark source as db_unavailable
FLASK_ENV=development
```

The auto-loader (`sitecustomize.py`) plus dashboard start-up will load this file. For VS Code debugging add:

```
{
   "python.envFile": "${workspaceFolder}/.env"
}
```

Security: Do not commit secrets—ensure `.env` is listed in `.gitignore`.