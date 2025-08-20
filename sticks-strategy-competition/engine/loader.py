from __future__ import annotations
import importlib.util
import ast
import sys
from pathlib import Path
from typing import List
from .strategy_interface import BaseStrategy
from .state import StrategyWrapper

BANNED_IMPORTS = {"os", "subprocess", "socket", "requests", "urllib", "pathlib", "sys"}


def scan_banned(path: Path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BANNED_IMPORTS:
                    raise ImportError(f"Banned import '{root}' in {path.name}")


def load_strategies(strategies_dir: Path) -> List[StrategyWrapper]:
    wrappers: List[StrategyWrapper] = []
    for p in strategies_dir.glob("*.py"):
        if p.name.startswith("__"):
            continue
        scan_banned(p)
        # Adapted for flattened structure: strategies located directly under strategies/
        # Keep backward compatibility: prefer strategies.<name>
        mod_name = f"strategies.{p.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, p)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)  # type: ignore
        cls = None
        for obj in module.__dict__.values():
            if isinstance(obj, type) and issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                cls = obj
                break
        if not cls:
            continue
        instance = cls()
        wrappers.append(StrategyWrapper(name=p.stem, module_name=mod_name, instance=instance))
    return wrappers
