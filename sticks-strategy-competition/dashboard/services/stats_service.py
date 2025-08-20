import os
from engine.file_stats import load_leaderboard
from engine.singlestore_repo import get_repo as get_ss_repo


def get_statistics():
    """Return statistics, preferring DB; optionally force DB only.

    Env:
      SKIT_FORCE_DB=1 -> if DB unavailable, raise (surface error to caller)
    """
    force_db = os.getenv("SKIT_FORCE_DB") == "1"
    repo = None
    try:
        repo = get_ss_repo()
    except Exception:
        repo = None
    if repo:
        try:
            leaderboard = repo.fetch_leaderboard()
            recent = repo.fetch_recent_games(limit=15)
            return {"leaderboard": leaderboard, "recent_games": recent, "source": "db"}
        except Exception:
            if force_db:
                raise
    if force_db:
        # Explicitly forced DB but not available or failed
        return {"leaderboard": [], "source": "db_unavailable"}
    # Fallback to file
    leaderboard = load_leaderboard()
    return {"leaderboard": leaderboard, "recent_games": [], "source": "file"}