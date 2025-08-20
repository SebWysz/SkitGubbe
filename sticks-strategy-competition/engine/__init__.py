"""Skitgubbe (sticks) engine package.

Initial experimental implementation of the two-part Skitgubbe game:
 Part 1: "Match If You Can"
 Part 2: "Beat It or Eat It"

Simplifications:
 - War resolution currently linear (no nested mini-trick object model)
 - Sloughing discretised into ordered rounds (not simultaneous free-for-all)

Future TODOs are marked in code.
"""

from .run_game import run_single_game  # convenience re-export

__all__ = ["run_single_game"]
