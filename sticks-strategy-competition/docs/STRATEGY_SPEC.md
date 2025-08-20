# SKITGUBBE STRATEGY SPECIFICATION

This document defines the strategy API and legality rules for the Skitgubbe (Flurst) engine in this repository. It supersedes any earlier "sticks" game specification.

## Parts of the Game
Play occurs in two sequential phases with different decision APIs:
1. Part 1 – Match If You Can (with wars on ties)
2. Part 2 – Beat It or Eat It (runs vs. eating lowest touching span)

## Strategy Class Structure
Each strategy is a Python module placed under `strategies/` which defines a class named `Strategy` (or assigns `Strategy = MyClass`). The class must implement the interface in `engine/strategy_interface.py` by subclassing `BaseStrategy` and providing:

```
class Strategy(BaseStrategy):
  name = "DescriptiveName"
  def part1_play(self, state) -> Part1PlayAction: ...
  def part1_slough(self, state) -> Part1SloughAction | None: ...
  def part2_move(self, state) -> Part2Action: ...
```

Internal mutable memory may be kept in `self.memory` (a dict) and is surfaced back to the engine through state views each call.

## Part 1 State (`Part1StateView`)
Fields available:
* `hand`: current hand (draws applied after plays/sloughs where applicable)
* `deck_remaining`: count of undealt cards (excludes face-down set-aside trump card)
* `current_trick_plays`: ordered plays (list of TrickPlay objects) including any sloughed cards
* `have_played_this_trick`: whether this player has made at least one required play in the current trick
* `allowed_slough_indices`: indices in `hand` that may be sloughed this slough round
* `players_card_counts`: current hand sizes of all players
* `collected_counts`: number of cards captured so far by each player
* `war_active`: whether a war is ongoing
* `memory`: strategy private dict

### Part 1 Actions
`Part1PlayAction` types:
* `PLAY_HAND_CARD` with `card_index`
* `PLAY_DECK_TOP` (draw and immediately play the next deck card; if deck empty it's illegal)

`Part1SloughAction`: list of additional matching rank cards to discard (optional each slough round).

### Leading Card Match Rule (Strict)
Identify the current leading (highest) rank already played in this trick. If you hold at least one card of that leading rank you MUST play one of them. You may not draw from deck nor play a different rank in that circumstance. If you hold none of the leading rank you may play any hand card or (if the deck is non-empty) draw the deck top. Drawing from an empty deck is illegal.

### Wars
If after all active players have completed their first required play in a trick there are multiple highest cards (by Part1 rank ordering) those tied players enter a war. Only war participants keep playing required cards in rotation until a single highest emerges. All cards from the unresolved trick (including war escalations and sloughs) go to the eventual winner. (Variants with face-down burns are not yet implemented.)

### Sloughing
Discrete rounds after each required play allow discarding additional copies of ranks already on the table subject to legality constraints provided in `allowed_slough_indices`.

### End of Part 1
One card was set aside face-down at deal (the would-be trump indicator). It is awarded to the winner of the last completed trick, or to the goat (starting player) if no trick completed.

## Part 2 State (`Part2StateView`)
Fields:
* `hand`
* `trump`: the suit of the set-aside card
* `table_plays`: list of dicts `{player_index, cards}` for current unresolved plays
* `player_out`: boolean list
* `player_hand_counts`: current counts
* `memory`

### Part 2 Actions
`Part2Action` types:
* `PLAY_RUN` with indices of a single-suit consecutive run (Ace high ordering, 2 lowest)
* `EAT` to remove the lowest touching span currently on the table (or skip if empty per engine behavior)

### Part 2 Legality Rules (current)
* Runs must be strictly same suit, consecutive ranks (2..A ordering), no duplicates, and indices supplied in ascending part2 rank order.
* To beat current highest: (a) any trump run beats any non-trump; (b) if both trump or both non-trump, higher top card wins; tie on top card requires longer run to beat; otherwise cannot beat.
* If a submitted run does not beat highest, engine searches for any beating single or run; if one exists the submitted action is illegal; if none exist the player must `EAT` (engine currently raises if illegal instead of auto-converting; strategies should decide correctly).
* Eating removes the globally lowest touching span (same suit consecutive) from the table. If table empty, `EAT` acts as a skip.
* A "kill" occurs when table has as many plays as active players; killer collects nothing but clears table; same player leads unless they just went out.

## Randomness & Time Limits
Per-decision wall clock limit (default 50ms). No hard memory limits yet. Random strategies should consider seeding for reproducibility (future API may provide a seed in state).

## Banned Imports (initial pass)
Network, filesystem, process-control, and dynamic import manipulation libraries are disallowed (e.g., `os`, `subprocess`, `socket`, `requests`, `urllib`, `pathlib`, `sys`). The loader performs a shallow static scan; sandbox hardening to follow.

## Error Handling
Illegal actions raise `ValueError` and terminate the game run (tests rely on this). Tournament mode (future) will likely disqualify only the offending decision and assign loss.

## Strategy Memory
`state.memory` references the same dict object each call; mutate to persist learning between decisions within a single game instance only.

## Versioning
Specification version: 0.3 (strict leading-rank match enforced).

## Checklist for Strategy Authors
1. Provide `Strategy` class with name.
2. Avoid banned imports.
3. In Part1, if you play a hand card while matches exist, pick a matching rank.
4. In Part2, ensure runs are valid & actually beat when required; otherwise choose `EAT`.
5. Keep decisions under time limit.

## Example Minimal Strategy Skeleton
```python
from engine.strategy_interface import BaseStrategy
from engine.actions import Part1PlayAction, Part1PlayType, Part1SloughAction, Part2Action, Part2ActionType

class Strategy(BaseStrategy):
  name = "Example"
  def part1_play(self, state):
    ranks_on_table = {tp.card.rank for tp in state.current_trick_plays}
    matching = [i for i,c in enumerate(state.hand) if c.rank in ranks_on_table]
    if matching:
      return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=matching[0])
    return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=0)
  def part1_slough(self, state):
    return Part1SloughAction(card_indices=[])
  def part2_move(self, state):
    if not state.table_plays:
      return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[0])
    # simplistic: try single trump or eat
    for i,c in enumerate(state.hand):
      if c.suit == state.trump:
        return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[i])
    return Part2Action(type=Part2ActionType.EAT)
```

## Future Extensions (Preview)
* Strict draw-on-match toggle
* Detailed war metadata exposure
* Deterministic RNG seed injection
* Enhanced sandbox & disqualification protocol

---
End of spec.