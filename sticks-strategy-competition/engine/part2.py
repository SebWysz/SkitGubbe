from __future__ import annotations
from typing import List, Set
from .cards import Card, Suit, touching_run
from .state import Part2StateView, StrategyWrapper, IllegalActionError, ReplayEvent
from .actions import Part2Action, Part2ActionType
from .sandbox import run_with_timeout


class Part2Engine:
    def __init__(self, strategies: List[StrategyWrapper], collected: List[List[Card]],
                 initial_leader: int, trump: Suit, time_limit_ms: int, random_seed: int | None = None,
                 replay_enabled: bool = True, max_replay_events: int = 10000):
        # Core setup
        self.strategies = strategies
        self.hands = [sorted(cs, key=lambda c: (c.suit, c.part2_value())) for cs in collected]
        self.trump = trump
        self.leader = initial_leader
        self.table_plays: List[dict] = []
        self.out = [False] * len(strategies)
        self.time_limit_ms = time_limit_ms
        self.random_seed = random_seed
        # Counters
        self.kills = 0
        self.eats = 0
        self.order_out: List[int] = []
        self.plays_needed_to_kill = len(strategies)
        self.turn_counter = 0
        self.max_turns = 5000  # safeguard against pathological loops
        # Replay
        self.replay_enabled = replay_enabled
        self.max_replay_events = max_replay_events
        self.replay: list[ReplayEvent] = []

    def highest_play(self):
        if not self.table_plays:
            return None
        def strength(play):
            highest = max(play["cards"], key=lambda c: c.part2_value())
            return (highest.suit == self.trump, highest.part2_value())
        return max(self.table_plays, key=strength)

    def build_state(self, idx: int) -> Part2StateView:
        return Part2StateView(
            hand=list(self.hands[idx]),
            trump=self.trump,
            table_plays=[p.copy() for p in self.table_plays],
            player_out=list(self.out),
            player_hand_counts=[len(h) for h in self.hands],
            memory=self.strategies[idx].memory,
        )

    def legal_run(self, hand_snapshot: List[Card], indices: List[int]) -> bool:
        if not indices:
            return False
        if len(set(indices)) != len(indices):
            return False
        if any(i < 0 or i >= len(hand_snapshot) for i in indices):
            return False
        # must be ascending by part2_value
        if any(hand_snapshot[indices[i]].part2_value() > hand_snapshot[indices[i+1]].part2_value() for i in range(len(indices)-1)):
            return False
        cards = [hand_snapshot[i] for i in indices]
        return touching_run(cards)

    def beats(self, run_cards: List[Card]) -> bool:
        if not self.table_plays:
            return True
        hp = self.highest_play()
        hp_cards = hp["cards"]  # type: ignore
        hp_max = max(hp_cards, key=lambda c: c.part2_value())
        rc_max = max(run_cards, key=lambda c: c.part2_value())
        if rc_max.suit == self.trump and hp_max.suit != self.trump:
            return True
        if rc_max.suit != self.trump and hp_max.suit == self.trump:
            return False
        if rc_max.part2_value() != hp_max.part2_value():
            return rc_max.part2_value() > hp_max.part2_value()
        return len(run_cards) > len(hp_cards)

    def lowest_touching_span(self):
        if not self.table_plays:
            return None
        all_cards = []
        for p in self.table_plays:
            all_cards.extend(p["cards"])
        def order_key(c: Card):
            return (c.suit == self.trump, c.part2_value())
        all_sorted = sorted(all_cards, key=order_key)
        lowest = all_sorted[0]
        same_suit = sorted([c for c in all_cards if c.suit == lowest.suit], key=lambda c: c.part2_value())
        span = [lowest]
        i = same_suit.index(lowest)
        j = i - 1
        while j >= 0 and same_suit[j + 1].part2_value() - same_suit[j].part2_value() == 1:
            span.insert(0, same_suit[j])
            j -= 1
        k = i + 1
        while k < len(same_suit) and same_suit[k].part2_value() - same_suit[k - 1].part2_value() == 1:
            span.append(same_suit[k])
            k += 1
        return span

    def remove_cards_from_hand(self, idx: int, indices: List[int]) -> List[Card]:
        hand = self.hands[idx]
        cards = [hand[i] for i in indices]
        for i in sorted(indices, reverse=True):
            hand.pop(i)
        return cards

    def run(self):
        current_player = self.leader
        while True:
            self.turn_counter += 1
            if self.turn_counter > self.max_turns:
                raise RuntimeError("Exceeded maximum turns safeguard in Part2; possible infinite loop")
            if sum(1 for o in self.out if not o) == 1:
                loser = self.out.index(False)
                if self.replay_enabled and len(self.replay) < self.max_replay_events:
                    self.replay.append(ReplayEvent(phase="part2", turn=self.turn_counter, player=-1, type="summary", detail={
                        "loser": loser,
                        "order_out": self.order_out + [loser],
                        "kills": self.kills,
                        "eats": self.eats,
                        "turns": self.turn_counter,
                        "players_remaining": [i for i, o in enumerate(self.out) if not o],
                        "events": len(self.replay)
                    }))
                return loser, self.order_out, self.kills, self.eats
            if self.out[current_player]:
                current_player = (current_player + 1) % len(self.strategies)
                continue
            # Engine guard: if a player's hand is already empty (can occur after table clear/kill
            # sequencing before they were marked out), mark them out immediately and skip asking
            # the strategy for a move. This prevents strategies from being invoked with empty
            # hands and returning invalid indices like [0].
            if not self.hands[current_player]:
                if not self.out[current_player]:
                    self.out[current_player] = True
                    self.order_out.append(current_player)
                    if self.replay_enabled and len(self.replay) < self.max_replay_events:
                        self.replay.append(ReplayEvent(phase="part2", turn=self.turn_counter, player=current_player, type="player_out", detail={"guard": True}))
                current_player = (current_player + 1) % len(self.strategies)
                continue
            state = self.build_state(current_player)
            action: Part2Action = run_with_timeout(
                self.strategies[current_player].instance.part2_move,
                args=(state,),
                time_limit_ms=self.time_limit_ms,
            )
            if action.type == Part2ActionType.EAT:
                span = self.lowest_touching_span()
                if not span:
                    current_player = (current_player + 1) % len(self.strategies)
                    continue
                self.eats += 1
                if self.replay_enabled and len(self.replay) < self.max_replay_events:
                    self.replay.append(ReplayEvent(phase="part2", turn=self.turn_counter, player=current_player, type="eat", detail={"span": [{"rank": c.rank, "suit": int(c.suit)} for c in span]}))
                new_table = []
                for p in self.table_plays:
                    remaining = [c for c in p["cards"] if c not in span]
                    if remaining:
                        p["cards"] = remaining
                        new_table.append(p)
                self.table_plays = new_table
                if not self.table_plays:
                    current_player = (current_player + 1) % len(self.strategies)
                continue
            else:
                if action.run_card_indices is None:
                    raise IllegalActionError(f"{self.strategies[current_player].name}: PLAY_RUN requires indices")
                if not self.legal_run(state.hand, action.run_card_indices):
                    raise IllegalActionError(f"{self.strategies[current_player].name}: Illegal run indices={action.run_card_indices} hand_size={len(state.hand)}")
                run_cards = [state.hand[i] for i in action.run_card_indices]
                if self.table_plays:
                    if not self.beats(run_cards):
                        hand_cards = state.hand
                        by_suit: dict[Suit, list[tuple[int, Card]]] = {}
                        for idx, c in enumerate(hand_cards):
                            by_suit.setdefault(c.suit, []).append((idx, c))
                        can_beat = False
                        for suit, pairs in by_suit.items():
                            pairs.sort(key=lambda pc: pc[1].part2_value())
                            n = len(pairs)
                            values = [p[1].part2_value() for p in pairs]
                            start = 0
                            while start < n:
                                end = start
                                while end + 1 < n and values[end+1] == values[end] + 1:
                                    end += 1
                                for i in range(start, end+1):
                                    for j in range(i, end+1):
                                        segment = [pairs[k][1] for k in range(i, j+1)]
                                        if self.beats(segment):
                                            can_beat = True
                                            break
                                    if can_beat:
                                        break
                                if can_beat:
                                    break
                                start = end + 1
                            if can_beat:
                                break
                        if can_beat:
                            raise IllegalActionError(f"{self.strategies[current_player].name}: Non-beating run played while beating run exists indices={action.run_card_indices}")
                        else:
                            raise IllegalActionError(f"{self.strategies[current_player].name}: Must EAT (no beating run) instead of playing indices={action.run_card_indices}")
                played = self.remove_cards_from_hand(current_player, action.run_card_indices)
                self.table_plays.append({"player_index": current_player, "cards": played})
                if self.replay_enabled and len(self.replay) < self.max_replay_events:
                    # Determine beat reason (whether new highest).
                    if len(self.table_plays) == 1:
                        beat = True; beat_reason = "first"
                    else:
                        hp_cards = self.highest_play()["cards"]  # type: ignore
                        hp_max = max(hp_cards, key=lambda c: c.part2_value())
                        rc_max = max(played, key=lambda c: c.part2_value())
                        if rc_max.suit == self.trump and hp_max.suit != self.trump:
                            beat = True; beat_reason = "trump_over_nontrump"
                        elif rc_max.suit != self.trump and hp_max.suit == self.trump:
                            beat = False; beat_reason = "cannot_over_trump"
                        elif rc_max.part2_value() > hp_max.part2_value():
                            beat = True; beat_reason = "higher_value"
                        elif rc_max.part2_value() == hp_max.part2_value() and len(played) > len(hp_cards):
                            beat = True; beat_reason = "longer_run"
                        else:
                            beat = False; beat_reason = "not_higher"
                    self.replay.append(ReplayEvent(phase="part2", turn=self.turn_counter, player=current_player, type="run_play", detail={
                        "cards": [{"rank": c.rank, "suit": int(c.suit)} for c in played],
                        "beat": beat,
                        "beat_reason": beat_reason
                    }))
                if not self.hands[current_player]:
                    self.out[current_player] = True
                    self.order_out.append(current_player)
                    if self.replay_enabled and len(self.replay) < self.max_replay_events:
                        self.replay.append(ReplayEvent(phase="part2", turn=self.turn_counter, player=current_player, type="player_out", detail={}))
                if len(self.table_plays) == self.plays_needed_to_kill:
                    killer = current_player
                    self.kills += 1
                    self.table_plays.clear()
                    if self.replay_enabled and len(self.replay) < self.max_replay_events:
                        self.replay.append(ReplayEvent(phase="part2", turn=self.turn_counter, player=killer, type="kill", detail={"kills": self.kills}))
                    if self.out[killer]:
                        current_player = (killer + 1) % len(self.strategies)
                    else:
                        current_player = killer
                else:
                    current_player = (current_player + 1) % len(self.strategies)
