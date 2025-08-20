"""Project auto bootstrap.

Any Python process started from the project root will import this module (Python
will automatically look for `sitecustomize` on sys.path). We use it to load the
local `.env` file so environment variables (e.g. SINGLESTORE_URI) are available
without manually exporting them.

Safe: silently no-ops if python-dotenv or the .env file is absent.
"""
from __future__ import annotations
import os
from pathlib import Path

try:  # pragma: no cover - best effort
    from dotenv import load_dotenv  # type: ignore
except Exception:  # dotenv not installed
    load_dotenv = None  # type: ignore

if load_dotenv:
    # Walk upward from current working directory to locate .env up to project root heuristic
    candidates = []
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        candidates.append(p / '.env')
    # Also include directory containing this file
    candidates.append(Path(__file__).resolve().parent / '.env')
    seen = set()
    for env_path in candidates:
        if env_path in seen:
            continue
        seen.add(env_path)
        if env_path.exists():
            try:
                load_dotenv(env_path, override=False)
                # Provide visibility which .env was loaded. Use an env flag to silence if desired.
                if os.getenv('SKIT_DEBUG_ENV_LOAD','1') == '1':
                    print(f"[sitecustomize] Loaded .env from: {env_path}")
            except Exception:
                pass
            break
