"""Root-level sitecustomize shim.

Allows launching Python from the repository root (parent of
`sticks-strategy-competition/`) while still executing the project's
actual environment bootstrap that lives inside the package directory.

It loads and executes the inner `sticks-strategy-competition/sitecustomize.py`.
Safe no-op if that file is missing.
"""
from __future__ import annotations
from pathlib import Path

_inner = Path(__file__).resolve().parent / 'sticks-strategy-competition' / 'sitecustomize.py'
if _inner.exists():  # pragma: no cover
    code = _inner.read_text()
    exec(compile(code, str(_inner), 'exec'))
