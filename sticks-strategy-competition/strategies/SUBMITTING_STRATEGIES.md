# Submitting a Skitgubbe Strategy

This project runs automated tournaments between submitted strategies for the card game *Skitgubbe* (aka "sticks"). This guide explains how to create and submit a new strategy implementation.

---
## TL;DR
1. Copy the template below into a new file under `strategies/`, e.g. `my_clever_strategy.py`.
2. Implement a class that subclasses `engine.strategy_interface.BaseStrategy` and expose a module-level name `Strategy` pointing to that class.
3. Only use the public types provided (no importing private engine internals beyond allowed modules).
4. Keep runtime under the time limit (default 50ms per engine callback) and avoid large memory objects (> ~1GB cap).
5. Open a PR with just your strategy file (and optional README snippet) – no engine modifications.

---
## File / Module Requirements
A valid strategy module (e.g. `strategies/my_strategy.py`) MUST:
- Import `BaseStrategy` from `engine.strategy_interface`.
- Implement all abstract methods:
  - `part1_play(self, state: Part1StateView) -> Part1PlayAction`
  - `part1_slough(self, state: Part1StateView) -> Part1SloughAction`
  - `part2_move(self, state: Part2StateView) -> Part2Action`
- Define a module-level symbol `Strategy = YourClassName`.
- Not perform side effects at import time (heavy I/O, network). Light constant initialization is fine.

Example minimal header:
```python
from engine.strategy_interface import BaseStrategy
from engine.actions import Part1PlayAction, Part1PlayType, Part1SloughAction, Part2Action, Part2ActionType

class MyStrategy(BaseStrategy):
    def part1_play(self, state):
        # TODO implement
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=0)
    def part1_slough(self, state):
        return Part1SloughAction(card_indices=[])
    def part2_move(self, state):
        return Part2Action(type=Part2ActionType.EAT)

Strategy = MyStrategy
```

---
## Public Types & What You Receive
Your strategy methods receive a *state view* object containing only the information you're allowed to see (perfect information is NOT given). All types are imported from `engine` submodules.

### Cards & Suits
`engine.cards`:
- `Card` (fields: `rank: str`, `suit: Suit`)
- `Suit` (IntEnum: `CLUBS, DIAMONDS, HEARTS, SPADES`)
Utility rank orders:
- Part 1 (trick phase): Ace low ordering (`A 2 3 4 5 6 7 8 9 10 J Q K`)
- Part 2 (shedding phase): Ace high ordering (`2 3 4 5 6 7 8 9 10 J Q K A`)
Methods: `card.part1_value()`, `card.part2_value()`, and `str(card)` convenience.

### Actions
`engine.actions`:
- Part 1:
  - `Part1PlayAction(type: Part1PlayType, card_index: Optional[int])`
    - `Part1PlayType.PLAY_HAND_CARD` must set `card_index`
    - `Part1PlayType.PLAY_DECK_TOP` ignores `card_index`
  - `Part1SloughAction(card_indices: List[int])` (indices into current `state.hand` snapshot). Only choose from `state.allowed_slough_indices`.
- Part 2:
  - `Part2Action(type: Part2ActionType, run_card_indices: Optional[List[int]])`
    - `Part2ActionType.PLAY_RUN` must provide `run_card_indices` (indices into hand forming a legal run / single that beats current table)
    - `Part2ActionType.EAT` ignores `run_card_indices`

### State Views
`engine.state`:
- `Part1StateView` fields:
  - `hand: List[Card]`
  - `deck_remaining: int`
  - `current_trick_plays: List[TrickPlay]` where each has `player_index, card, sequence`
  - `have_played_this_trick: bool`
  - `allowed_slough_indices: List[int]` (subset of indices in `hand` allowed to slough now)
  - `players_card_counts: List[int]` (hand sizes of each player)
  - `collected_counts: List[int]` (how many capturings/tricks each player has collected)
  - `war_active: bool` (True if in a war sub-sequence)
  - `memory: Dict[str, Any]` (shared persistent memory reference)
- `Part2StateView` fields:
  - `hand: List[Card]`
  - `trump: Suit`
  - `table_plays: List[dict]` each with `{player_index:int, cards: List[Card]}` in play order
  - `player_out: List[bool]` (True if player done / out)
  - `player_hand_counts: List[int]`
  - `memory: Dict[str, Any]`

### Memory Persistence
Each strategy instance has `self.memory: dict`. The same dict is also passed back via `state.memory` for convenience. Use this to store learned patterns, counts, or heuristics across calls *within a single game*. (Not persisted across games yet.) Keep it lightweight.

---
## Engine Call Sequence (High Level)
1. Part 1 (Trick Phase)
   - Repeated cycles of `part1_play` for each player in order until trick resolves.
   - Possible "war" situations (tie on highest rank) extend trick: `war_active` becomes True.
   - After winning trick final card draw/slough phase triggers `part1_slough` for holder (if allowed) to discard down to limits.
2. Transition: Last trick winner (or goat) leads Part 2.
3. Part 2 (Shedding Phase)
   - Players attempt to play *runs* (consecutive same-suit sequences) or single cards beating previous top by rank (or trump vs non-trump). If unable or choose not to: `EAT` (take table into hand).
   - Eliminations when a player empties their hand; final remaining player is the loser.

---
## Legality & Validation
The engine enforces legality; if you return an illegal action (bad indices, wrong card, invalid run) the engine will raise an error and your strategy will lose (or be penalized). Safest practice:
- Always ensure indices refer to current `state.hand` (which changes after each action globally). Copy indexes before mutating internal plans.
- For Part 1 plays: if forced to match a current leading rank, you must choose a card of that rank if you hold one.
- For Part 2 plays: Provide ascending consecutive same-suit run OR single; engine decides beating validity.

---
## Randomness
If you use randomness, prefer the standard `random` module. Tournaments often set `random_seed` for reproducibility across games.

---
## Time & Memory Constraints
- Soft per-call time limit: `GameConfig.time_limit_ms` (default 50ms). Use efficient logic (avoid O(n^3) scans of full hand repeatedly; hand size is limited but still be prudent).
- Memory: Avoid storing huge arrays; engine may in future enforce `max_memory_bytes`.

---
## Template (Fully Commented)
Save this as `strategies/my_strategy.py`.
```python
from __future__ import annotations
import random
from engine.strategy_interface import BaseStrategy
from engine.actions import (
    Part1PlayAction, Part1PlayType,
    Part1SloughAction,
    Part2Action, Part2ActionType,
)

class MyStrategy(BaseStrategy):
    """Example strategy template.

    Replace decision logic with something smarter. Use self.memory to persist
    per-game info (counts, seen ranks, etc.).
    """

    def part1_play(self, state):
        # If we must match rank already led (strict rule) attempt that first.
        if state.current_trick_plays:
            leading_rank = max(state.current_trick_plays, key=lambda tp: tp.card.part1_value()).card.rank
            rank_matches = [i for i, c in enumerate(state.hand) if c.rank == leading_rank]
            if rank_matches:
                # Simple heuristic: play lowest value among required rank
                choice = min(rank_matches, key=lambda i: state.hand[i].part1_value())
                return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=choice)
        # Optional: sometimes draw from deck if available early
        if state.deck_remaining > 0 and random.random() < 0.2:
            return Part1PlayAction(type=Part1PlayType.PLAY_DECK_TOP)
        # Fallback: play lowest valued card
        lowest = min(range(len(state.hand)), key=lambda i: state.hand[i].part1_value())
        return Part1PlayAction(type=Part1PlayType.PLAY_HAND_CARD, card_index=lowest)

    def part1_slough(self, state):
        # Example: slough nothing (conservative). Could discard duplicates, etc.
        return Part1SloughAction(card_indices=[])

    def part2_move(self, state):
        # If table empty: lead lowest single card
        if not state.table_plays:
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[self._lowest_index(state)])
        # Try to beat current highest single/run with a single card (simplistic)
        trump = state.trump
        def play_strength(play):
            top = max(play['cards'], key=lambda c: c.part2_value())
            return (top.suit == trump, top.part2_value())
        highest_play = max(state.table_plays, key=play_strength)
        cur_strength = play_strength(highest_play)
        candidates = []
        for i, c in enumerate(state.hand):
            s = (c.suit == trump, c.part2_value())
            if s[0] and not cur_strength[0]:
                candidates.append(i)
            elif s[0] == cur_strength[0] and s[1] > cur_strength[1]:
                candidates.append(i)
        if candidates:
            # choose minimal winning card
            best = min(candidates, key=lambda i: state.hand[i].part2_value())
            return Part2Action(type=Part2ActionType.PLAY_RUN, run_card_indices=[best])
        # Otherwise eat
        return Part2Action(type=Part2ActionType.EAT)

    def _lowest_index(self, state):
        return min(range(len(state.hand)), key=lambda i: state.hand[i].part1_value())

Strategy = MyStrategy
```

---
## Testing Your Strategy Locally
1. Run a single game for a smoke test:
```bash
python -m engine.run_game
```
2. Run a tournament: 
```bash
python scripts/run_tournament.py
```
3. Visit the dashboard (after generating some stats):
```bash
python dashboard/app.py
```

---
## Submission Checklist
- [ ] File placed in `strategies/` and named `your_strategy_name.py` (no spaces).
- [ ] Contains `Strategy = YourClass` at module bottom.
- [ ] No external network / disk I/O in decision methods.
- [ ] Passes `pytest` locally (does not break existing tests).
- [ ] Executes within time limits.
- [ ] No modification to engine core files.

---
## FAQ
**Q: Can I cache across games?** Not yet; memory resets per game instance.

**Q: Can I import numpy/pandas?** Only if already in dependencies; heavy libs discouraged for fairness. Keep logic lightweight.

**Q: What if my strategy errors?** It's treated as a loss for that game; ensure robust try/except internally if doing risky logic.

**Q: How do I detect wars?** In Part 1, `state.war_active` tells you if the current trick is in war resolution.

**Q: How can I estimate opponents' hands?** Track `players_card_counts` / `player_hand_counts` and cards seen in `current_trick_plays` / `table_plays` and store summaries in `self.memory`.

---
## Need More Info?
Open an issue or PR with questions. Happy hacking!
