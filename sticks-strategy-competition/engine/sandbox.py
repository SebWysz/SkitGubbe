from __future__ import annotations
import multiprocessing as mp
from typing import Callable
from .state import TimeoutEngineError, StrategyExecutionError


def _invoke(fn, args, kwargs, q):
    try:
        q.put(("ok", fn(*args, **(kwargs or {}))))
    except Exception as e:  # pragma: no cover - defensive
        q.put(("err", repr(e)))


def run_with_timeout(fn: Callable, args=(), kwargs=None, time_limit_ms: int = 50):
    """Execute fn(*args, **kwargs) in a subprocess with a wall time limit.

    NOTE: Memory limiting & banned import enforcement to be enhanced later.
    """
    if kwargs is None:
        kwargs = {}
    q: mp.Queue = mp.Queue()
    proc = mp.Process(target=_invoke, args=(fn, args, kwargs, q))
    proc.start()
    proc.join(time_limit_ms / 1000.0)
    if proc.is_alive():
        proc.terminate()
    if proc.exitcode is None:
        proc.join()
    if proc.exitcode != 0 and proc.exitcode is not None:
        raise TimeoutEngineError("Strategy action timed out or crashed")
    if q.empty():
        raise StrategyExecutionError("Strategy produced no result")
    status, payload = q.get()
    if status == "err":
        raise StrategyExecutionError(f"Strategy error: {payload}")
    return payload
