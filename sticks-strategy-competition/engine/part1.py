from __future__ import annotations
import random
from typing import List, Optional
from .cards import Card, make_deck
from .state import StrategyWrapper, Part1StateView, TrickPlay, IllegalActionError, ReplayEvent
from .actions import Part1PlayAction, Part1PlayType, Part1SloughAction
from .sandbox import run_with_timeout


class Part1Engine:
    """Simplified Part 1 (Match If You Can) implementation.

    TODO: Implement full war mini-trick structure & nuanced slough legality.
    """

    def __init__(self, strategies: List[StrategyWrapper], goat_index: int, time_limit_ms: int,
                 random_seed: int | None = None, replay_enabled: bool = True, max_replay_events: int = 10000):
        # Core config
        self.strategies = strategies
        self.goat_index = goat_index
        self.time_limit_ms = time_limit_ms
        self.random_seed = random_seed
        self._rng = random.Random(random_seed)
        # Piles / hands
        self.deck: List[Card] = []
        self.hands: List[List[Card]] = [[] for _ in strategies]
        self.collected: List[List[Card]] = [[] for _ in strategies]
        # Trick / war bookkeeping
        self.trick_seq = 0
        self.current_trick: List[TrickPlay] = []
        self.last_completed_trick_winner: Optional[int] = None
        self.wars = 0
        self.set_aside_card: Card | None = None
        self.war_active: bool = False
        self.war_participants: List[int] = []
        self.war_turn_index: int = 0
        # Replay
        self.replay_enabled = replay_enabled
        self.max_replay_events = max_replay_events
        self.replay: list[ReplayEvent] = []

    def deal(self):
        self.deck = make_deck()
        self._rng.shuffle(self.deck)
        for _ in range(3):
            for h in self.hands:
                h.append(self.deck.pop())
        self.set_aside_card = self.deck.pop()  # face-down trump card

    def build_state(self, idx: int) -> Part1StateView:
        hand = list(self.hands[idx])
        deck_remaining = len(self.deck)
        have_played = any(tp.player_index == idx for tp in self.current_trick if (not self.war_active) or tp.sequence.is_integer())
        current_high_rank = None
        if self.current_trick:
            high = max(self.current_trick, key=lambda tp: tp.card.part1_value())
            current_high_rank = high.card.rank
        ranks_on_table = {tp.card.rank for tp in self.current_trick}
        allowed_slough: List[int] = []
        for i, c in enumerate(hand):
            if c.rank in ranks_on_table:
                # cannot pre-slough potential required match before first personal play of trick
                if current_high_rank and c.rank == current_high_rank and not have_played:
                    continue
                # if war active and player is participant, prevent sloughing last card when deck empty
                if self.war_active and idx in self.war_participants and not self.deck and len(hand) == 1:
                    continue
                allowed_slough.append(i)
        return Part1StateView(
            hand=hand,
            deck_remaining=deck_remaining,
            current_trick_plays=list(self.current_trick),
            have_played_this_trick=have_played,
            allowed_slough_indices=allowed_slough,
            players_card_counts=[len(h) for h in self.hands],
            collected_counts=[len(c) for c in self.collected],
            war_active=self.war_active,
            memory=self.strategies[idx].memory,
        )

    def play_turn(self, player_index: int):
        """Execute a required play (not a slough) for player_index.

        When in a war, only war participants are allowed to play_turn.
        """
        if self.war_active and player_index not in self.war_participants:
            return  # safety no-op
        strat = self.strategies[player_index]
        state = self.build_state(player_index)
        action: Part1PlayAction = run_with_timeout(
            strat.instance.part1_play,
            args=(state,),
            time_limit_ms=self.time_limit_ms,
        )
        # Strict leading-card match rule:
        # If there is a current trick, identify the highest (leading) rank. If player holds one or more
        # cards of that rank, they MUST play one of them (cannot draw deck or play a different rank).
        hand = self.hands[player_index]
        if self.current_trick:
            high_play = max(self.current_trick, key=lambda tp: tp.card.part1_value())
            leading_rank = high_play.card.rank
            leading_indices = [i for i, c in enumerate(hand) if c.rank == leading_rank]
        else:
            leading_indices = []
        if leading_indices:
            if action.type != Part1PlayType.PLAY_HAND_CARD:
                raise IllegalActionError("Illegal: must play a card matching the leading (highest) rank")
            if action.card_index is None or action.card_index not in leading_indices:
                raise IllegalActionError("Illegal: chosen card does not match leading rank")
        else:
            # No leading-rank card in hand (or empty trick). If drawing, deck must be non-empty.
            if action.type == Part1PlayType.PLAY_DECK_TOP and not self.deck:
                raise IllegalActionError("Illegal: deck empty; cannot play deck top")
        if action.type == Part1PlayType.PLAY_DECK_TOP:
            card = self.deck.pop()
        else:
            if action.card_index is None or action.card_index >= len(hand):
                raise IllegalActionError("Invalid hand card index")
            card = hand.pop(action.card_index)
            if self.deck:
                hand.append(self.deck.pop())
        self.trick_seq += 1
        self.current_trick.append(TrickPlay(player_index, card, float(self.trick_seq)))
        if self.replay_enabled and len(self.replay) < self.max_replay_events:
            self.replay.append(ReplayEvent(phase="part1", turn=self.trick_seq, player=player_index, type="play", detail={"rank": card.rank, "suit": int(card.suit), "deck_draw": action.type == Part1PlayType.PLAY_DECK_TOP}))

    def slough_round(self) -> bool:
        changed = False
        for i, _ in enumerate(self.strategies):
            state = self.build_state(i)
            if not state.allowed_slough_indices:
                continue
            action: Part1SloughAction = run_with_timeout(
                self.strategies[i].instance.part1_slough,
                args=(state,),
                time_limit_ms=self.time_limit_ms,
            )
            if any(ci not in state.allowed_slough_indices for ci in action.card_indices):
                raise IllegalActionError("Illegal slough indices")
            for ci in sorted(action.card_indices, reverse=True):
                card = self.hands[i].pop(ci)
                self.current_trick.append(TrickPlay(i, card, self.trick_seq + 0.1))
                if self.deck:
                    self.hands[i].append(self.deck.pop())
                changed = True
                if self.replay_enabled and len(self.replay) < self.max_replay_events:
                    self.replay.append(ReplayEvent(phase="part1", turn=self.trick_seq, player=i, type="slough", detail={"rank": card.rank, "suit": int(card.suit)}))
        return changed

    def resolve_or_continue(self):
        """Evaluate current trick state for end, war start, or continuing war.

        Returns (ended, winner_index|None)
        """
        if not self.current_trick:
            return False, None
        # Consider only latest plays for war participants when war active
        high_val = max(tp.card.part1_value() for tp in self.current_trick)
        highs = [tp for tp in self.current_trick if tp.card.part1_value() == high_val]
        if self.war_active:
            # Filter highs to only those whose player is still in war participants
            highs = [h for h in highs if h.player_index in self.war_participants]
            if len(highs) == 1:
                # War resolved
                winner = highs[0].player_index
                collected_cards = [tp.card for tp in self.current_trick]
                self.collected[winner].extend(collected_cards)
                self.current_trick.clear()
                self.last_completed_trick_winner = winner
                self.war_active = False
                self.war_participants.clear()
                self.war_turn_index = 0
                return True, winner
            else:
                # Continue war: restrict participants to tied highs
                self.war_participants = [h.player_index for h in highs]
                self.war_turn_index = 0
                return False, None
        else:
            # Don't resolve a trick until all active players (with cards) have played once
            active_players = [i for i, h in enumerate(self.hands) if h]
            distinct_played = {tp.player_index for tp in self.current_trick}
            if not all(p in distinct_played for p in active_players):
                return False, None
            if len(highs) == 1:
                winner = highs[0].player_index
                collected_cards = [tp.card for tp in self.current_trick]
                self.collected[winner].extend(collected_cards)
                self.current_trick.clear()
                self.last_completed_trick_winner = winner
                return True, winner
            else:
                # Initiate war among tied highs
                self.wars += 1
                self.war_active = True
                ordered_players = []
                # Determine order starting from first appearance of first high card
                first_high_seq = min(h.sequence for h in highs)
                first_high_player = [h for h in highs if h.sequence == first_high_seq][0].player_index
                # Build seating order starting at that player among tied highs preserving table order
                start_index = first_high_player
                n = len(self.strategies)
                for offset in range(n):
                    pi = (start_index + offset) % n
                    if any(h.player_index == pi for h in highs):
                        ordered_players.append(pi)
                self.war_participants = ordered_players
                self.war_turn_index = 0
                if self.replay_enabled and len(self.replay) < self.max_replay_events:
                    self.replay.append(ReplayEvent(phase="part1", turn=self.trick_seq, player=-1, type="war_start", detail={"participants": ordered_players}))
                return False, None

    def run(self):
        self.deal()
        leader = self.goat_index
        players_n = len(self.strategies)
        while True:
            empties = [i for i, h in enumerate(self.hands) if not h]
            if empties and not self.deck:
                # Abort unresolved trick: everyone reclaims their played cards
                for tp in self.current_trick:
                    self.collected[tp.player_index].append(tp.card)
                for i, h in enumerate(self.hands):
                    self.collected[i].extend(h)
                    self.hands[i].clear()
                break
            # Determine whose turn (normal or war)
            if self.war_active:
                current_player = self.war_participants[self.war_turn_index]
                self.play_turn(current_player)
                # After play, offer slough rounds to all players
                while self.slough_round():
                    pass
                ended, winner = self.resolve_or_continue()
                if ended:
                    leader = winner  # next leader for next trick
                else:
                    # advance war pointer
                    self.war_turn_index = (self.war_turn_index + 1) % len(self.war_participants)
            else:
                self.play_turn(leader)
                while self.slough_round():
                    pass
                ended, winner = self.resolve_or_continue()
                if ended:
                    leader = winner  # type: ignore
                else:
                    leader = (leader + 1) % players_n
        if self.last_completed_trick_winner is not None and self.set_aside_card:
            self.collected[self.last_completed_trick_winner].append(self.set_aside_card)
        else:
            # Edge: no completed trick; just assign trump card to goat for part2
            if self.set_aside_card:
                self.collected[self.goat_index].append(self.set_aside_card)
                self.last_completed_trick_winner = self.goat_index
        # Append summary replay event
        if self.replay_enabled and len(self.replay) < self.max_replay_events:
            try:
                trump_info = {"rank": self.set_aside_card.rank, "suit": int(self.set_aside_card.suit)} if self.set_aside_card else None
            except Exception:
                trump_info = None
            self.replay.append(ReplayEvent(
                phase="part1",
                turn=self.trick_seq,
                player=-1,
                type="summary",
                detail={
                    "wars": self.wars,
                    "last_trick_winner": self.last_completed_trick_winner,
                    "tricks_played": self.trick_seq,
                    "collected_counts": [len(c) for c in self.collected],
                    "trump_card": trump_info,
                }
            ))
        return self.collected, self.last_completed_trick_winner, self.set_aside_card, self.wars
