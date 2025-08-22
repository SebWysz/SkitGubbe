from __future__ import annotations
from pathlib import Path
import sys
import argparse

# Ensure project root (parent of this scripts dir) is on sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.loader import load_strategies  # noqa: E402
from engine.tournament import run_tournament, TournamentConfig  # noqa: E402


def parse_args(argv: list[str] | None = None):  # pragma: no cover - thin wrapper
    p = argparse.ArgumentParser(description="Run a Skitgubbe strategy tournament")
    p.add_argument('--games', type=int, default=20, help='Number of games to run (default: 20)')
    p.add_argument('--seed', type=int, default=42, help='Base random seed (default: 42)')
    p.add_argument('--time-limit-ms', type=int, default=60, help='Per-call soft time limit ms (default: 60)')
    p.add_argument('--no-rotate-goat', action='store_true', help='Disable rotating the initial goat position')
    p.add_argument('--replay', action='store_true', help='Enable replay recording (slower)')
    p.add_argument('--include', type=str, default='', help='Comma-separated subset of strategy module basenames (without .py) to include')
    p.add_argument('--list', action='store_true', help='List discovered strategies and exit')
    p.add_argument('--progress', action='store_true', help='Show live per-game progress updating one line')
    p.add_argument('--show-segmented', action='store_true', help='Show separate leaderboards for 3, 4, 5 player games')
    p.add_argument('--players', type=int, default=5, choices=[3, 4, 5], help='Number of players per game (default: 5)')
    return p.parse_args(argv)


def filter_wrappers(wrappers, include_csv: str):  # pragma: no cover - simple filter
    if not include_csv:
        return wrappers
    wanted = {w.strip() for w in include_csv.split(',') if w.strip()}
    return [w for w in wrappers if w.name in wanted]


def main(argv: list[str] | None = None):  # pragma: no cover
    args = parse_args(argv)
    strategies_dir = Path(__file__).parent.parent / 'strategies'
    wrappers = load_strategies(strategies_dir)
    if args.list:
        print('Discovered strategies:')
        for w in wrappers:
            print(' -', w.name)
        return 0
    wrappers = filter_wrappers(wrappers, args.include)
    if len(wrappers) < args.players:
        raise SystemExit(f'Need at least {args.players} strategies to run {args.players}-player games (after filtering)')
    cfg = TournamentConfig(
        games=args.games,
        random_seed=args.seed,
        time_limit_ms=args.time_limit_ms,
        enable_replay=args.replay,
        rotate_goat=not args.no_rotate_goat,
    )
    results = run_tournament(wrappers, cfg, max_players_per_game=args.players, progress=args.progress)
    print("Leaderboard (by loss rate):")
    for i, row in enumerate(results['leaderboard'], 1):
        print(f"{i:2d}. {row['name']}: loss_rate={row['loss_rate']:.3f} avg_pos={row['avg_finish_position']:.2f} games={row['games']}")
    
    if args.show_segmented and 'segmented' in results:
        print("\nSegmented Leaderboards by Player Count:")
        for bucket in sorted(results['segmented'].keys()):
            players = bucket[1:] if bucket.startswith('p') else bucket  # strip 'p' prefix
            print(f"\n{players}-Player Games:")
            seg_lb = results['segmented'][bucket]
            if seg_lb:
                for i, row in enumerate(seg_lb, 1):
                    print(f"{i:2d}. {row['name']}: loss_rate={row['loss_rate']:.3f} avg_pos={row['avg_finish_position']:.2f} games={row['games']}")
            else:
                print("  (no games recorded)")
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
