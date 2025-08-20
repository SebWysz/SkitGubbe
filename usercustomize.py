"""Root-level usercustomize shim.

Python imports `usercustomize` (after `sitecustomize`) if present. We use this
so that running `python` from the repository root still triggers the project's
inner environment bootstrap (found in `sticks-strategy-competition/sitecustomize.py`).
"""
from __future__ import annotations
from pathlib import Path

_inner_site = Path(__file__).resolve().parent / 'sticks-strategy-competition' / 'sitecustomize.py'
if _inner_site.exists():  # pragma: no cover
    code = _inner_site.read_text()
    exec(compile(code, str(_inner_site), 'exec'))
