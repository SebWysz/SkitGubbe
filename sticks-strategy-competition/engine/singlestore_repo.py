from __future__ import annotations

"""SingleStore stats repository using native singlestoredb driver only.

Connection pattern strictly follows the requested format:

    import singlestoredb as s2
    conn = s2.connect(SINGLESTORE_URI)
    with conn:
        with conn.cursor() as cur:
            cur.is_connected()

We open short‑lived connections per operation (record / fetch) to keep it
simple and resilient. If the environment variable SINGLESTORE_URI is missing
or a connection fails, caller gets None and higher layers will fall back to
file based stats.
"""

import os
from pathlib import Path
import json
import logging
from typing import Optional, List, Dict, Any

import singlestoredb as s2
try:  # Attempt early .env load (best effort). We keep very quiet here.
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / '.env', override=False)
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore

log = logging.getLogger(__name__)

SCHEMA_GAME = (
    "CREATE TABLE IF NOT EXISTS game_records ("
    "id BIGINT AUTO_INCREMENT PRIMARY KEY,"
    "seed BIGINT NULL,"
    "goat_index INT NOT NULL,"
    "loser VARCHAR(128) NOT NULL,"
    "wars INT NOT NULL,"
    "kills INT NOT NULL,"
    "eats INT NOT NULL,"
    "trump VARCHAR(16) NULL,"
    "order_out JSON NOT NULL,"
    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    ") ENGINE=ColumnStore;"
)
SCHEMA_AGG = (
    "CREATE TABLE IF NOT EXISTS aggregated_stats ("
    "strategy VARCHAR(128) PRIMARY KEY,"
    "games BIGINT NOT NULL DEFAULT 0,"
    "losses BIGINT NOT NULL DEFAULT 0,"
    "positions_sum BIGINT NOT NULL DEFAULT 0,"
    "wars DOUBLE NOT NULL DEFAULT 0,"
    "kills DOUBLE NOT NULL DEFAULT 0,"
    "eats DOUBLE NOT NULL DEFAULT 0,"
    "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
    ") ENGINE=ColumnStore;"
)

class SingleStoreStatsRepo:
    def __init__(self, uri: str):
        self.uri = self._normalize_uri(uri)
        self._ensure_schema()

    def _connect(self):
        return s2.connect(self.uri)

    @staticmethod
    def _normalize_uri(uri: str) -> str:
        return uri.strip()

    def _ensure_schema(self):
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(SCHEMA_GAME)
                    cur.execute(SCHEMA_AGG)
        except Exception as e:  # pragma: no cover
            log.warning("Failed ensuring SingleStore schema: %s", e)
            raise

    def record_game(self, result: dict, seed: int | None, goat_index: int):
        order_json = json.dumps(result['order_out'])
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    # game record
                    cur.execute(
                        "INSERT INTO game_records(seed, goat_index, loser, wars, kills, eats, trump, order_out) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (seed, goat_index, result['loser'], result['wars'], result['kills'], result['eats'], result['trump'], order_json)
                    )
                    # aggregation
                    order = result['order_out'] + [result['loser']]
                    wars = result['wars']; kills = result['kills']; eats = result['eats']; n = len(order)
                    for pos, name in enumerate(order):
                        cur.execute(
                            "INSERT INTO aggregated_stats(strategy,games,losses,positions_sum,wars,kills,eats) "
                            "VALUES(%s,1,%s,%s,%s,%s,%s) "
                            "ON DUPLICATE KEY UPDATE "
                            "games=games+1, losses=losses+VALUES(losses), positions_sum=positions_sum+VALUES(positions_sum), "
                            "wars=wars+VALUES(wars), kills=kills+VALUES(kills), eats=eats+VALUES(eats)",
                            (name, 1 if pos == n-1 else 0, pos, wars / n, kills / n, eats / n)
                        )
                # context manager commits automatically
        except Exception as e:  # pragma: no cover
            log.warning("Failed recording game to SingleStore: %s", e)
            raise

    def fetch_leaderboard(self) -> list[dict]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT strategy,games,losses,positions_sum,wars,kills,eats FROM aggregated_stats")
                    rows = cur.fetchall()
        except Exception as e:  # pragma: no cover
            log.warning("Failed fetching leaderboard from SingleStore: %s", e)
            return []
        lb: list[dict] = []
        for (strategy, games, losses, pos_sum, wars, kills, eats) in rows:
            games = games or 1
            lb.append({
                'strategy': strategy,
                'games': games,
                'losses': losses,
                'loss_rate': losses / games,
                'avg_finish_position': pos_sum / games,
                'avg_wars': wars / games,
                'avg_kills': kills / games,
                'avg_eats': eats / games,
            })
        lb.sort(key=lambda x: (x['loss_rate'], x['avg_finish_position']))
        return lb

    def fetch_recent_games(self, limit: int = 20) -> list[dict]:
        """Return a list of recent games (most recent first).

        Includes: id, created_at, seed, goat_index, wars, kills, eats, trump,
        players (ordered list of all players, last element is loser), loser.
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, seed, goat_index, loser, wars, kills, eats, trump, order_out, created_at "
                        "FROM game_records ORDER BY id DESC LIMIT %s", (limit,)
                    )
                    rows = cur.fetchall()
        except Exception as e:  # pragma: no cover
            log.warning("Failed fetching recent games from SingleStore: %s", e)
            return []
        recent: list[dict] = []
        for (gid, seed, goat_idx, loser, wars, kills, eats, trump, order_json, created_at) in rows:
            try:
                order_out = json.loads(order_json) if isinstance(order_json, str) else order_json
            except Exception:
                order_out = []
            players = list(order_out) + [loser]
            recent.append({
                'id': gid,
                'seed': seed,
                'goat_index': goat_idx,
                'loser': loser,
                'wars': wars,
                'kills': kills,
                'eats': eats,
                'trump': trump,
                'players': players,
                'created_at': created_at.isoformat() if hasattr(created_at, 'isoformat') else created_at,
            })
        return recent

def get_repo() -> SingleStoreStatsRepo | None:
    uri = os.getenv("SINGLESTORE_URI")
    if not uri and os.getenv('SKIT_AUTO_LOAD_DOTENV','1') == '1':
        # Secondary attempt: manually search upward for a .env and parse SINGLESTORE_URI
        root_candidates: list[Path] = []
        # Start from CWD and walk upward a few levels
        cwd = Path.cwd()
        for p in [cwd] + list(cwd.parents)[:5]:  # limit depth
            root_candidates.append(p / '.env')
        # Also include project package root relative to this file
        root_candidates.append(Path(__file__).resolve().parents[2] / '.env')
        seen: set[Path] = set()
        for candidate in root_candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate.exists():
                try:
                    # Use python-dotenv if available for robust parsing; else do minimal line parse
                    if 'load_dotenv' in globals() and load_dotenv:  # type: ignore
                        load_dotenv(candidate, override=False)
                        uri = os.getenv("SINGLESTORE_URI")
                    else:  # manual parse
                        for line in candidate.read_text().splitlines():
                            if line.strip().startswith('SINGLESTORE_URI='):
                                uri = line.split('=',1)[1].strip().strip('"').strip("'")
                                break
                    if uri:
                        if os.getenv('SKIT_DEBUG_ENV_LOAD','1') == '1':
                            print(f"[singlestore_repo] Loaded SINGLESTORE_URI from .env at {candidate}")
                        break
                except Exception:
                    continue
    if not uri:
        return None
    # Ensure scheme is present; if missing, assume singlestoredb:// and warn
    if '://' not in uri:
        # print('[singlestore_repo] Warning: SINGLESTORE_URI missing scheme, prepending singlestoredb://')
        uri = 'singlestoredb://' + uri
    uri = uri.strip()
    try:
        with s2.connect(uri) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return SingleStoreStatsRepo(uri)
    except Exception as e:  # pragma: no cover
        log.warning("SingleStore repo unavailable: %s", e)
        return None

__all__ = ["get_repo", "SingleStoreStatsRepo"]
