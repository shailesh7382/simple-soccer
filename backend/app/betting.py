"""Betting engine.

Ties together the :class:`~app.blockchain.Blockchain`, the pluggable event
registry, and in-memory game state. Every placed bet and every settlement is
committed to the chain, making the betting record tamper-evident. Bets are
rejected once an event's ``lock_time`` has passed, satisfying the requirement
that betting cannot happen after the event.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from app.blockchain import Blockchain
from app.events.base import EventPlugin, PluginRegistry, registry


EVENT_OPEN = "open"
EVENT_LOCKED = "locked"
EVENT_SETTLED = "settled"

BET_ACTIVE = "active"
BET_WON = "won"
BET_LOST = "lost"


class BettingError(Exception):
    """Raised when a betting operation is not permitted."""


class GameEngine:
    """Holds events and bets, and enforces blockchain-backed betting rules."""

    def __init__(
        self,
        plugin_registry: PluginRegistry = registry,
        difficulty: int = 3,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.registry = plugin_registry
        self.chain = Blockchain(difficulty=difficulty)
        self.events: Dict[str, Dict[str, Any]] = {}
        self.bets: Dict[str, Dict[str, Any]] = {}
        self._clock = clock

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def _plugin_or_raise(self, type_id: str) -> EventPlugin:
        plugin = self.registry.get(type_id)
        if plugin is None:
            raise BettingError(f"Unknown event type '{type_id}'")
        return plugin

    def create_event(
        self,
        type_id: str,
        title: str,
        context: Dict[str, Any],
        lock_time: float,
    ) -> Dict[str, Any]:
        self._plugin_or_raise(type_id)
        event_id = uuid.uuid4().hex
        event = {
            "id": event_id,
            "type_id": type_id,
            "title": title,
            "context": dict(context),
            "lock_time": float(lock_time),
            "status": EVENT_OPEN,
            "outcome": None,
        }
        self.events[event_id] = event
        return self.event_view(event_id)

    def _event_or_raise(self, event_id: str) -> Dict[str, Any]:
        event = self.events.get(event_id)
        if event is None:
            raise BettingError(f"Unknown event '{event_id}'")
        return event

    def is_open_for_betting(self, event: Dict[str, Any]) -> bool:
        return event["status"] == EVENT_OPEN and self._clock() < event["lock_time"]

    def event_view(self, event_id: str) -> Dict[str, Any]:
        event = self._event_or_raise(event_id)
        plugin = self._plugin_or_raise(event["type_id"])
        # Reflect time-based locking in the reported status.
        status = event["status"]
        if status == EVENT_OPEN and self._clock() >= event["lock_time"]:
            status = EVENT_LOCKED
        return {
            **event,
            "status": status,
            "options": plugin.options(event["context"]),
            "open_for_betting": self.is_open_for_betting(event),
        }

    def list_events(self) -> List[Dict[str, Any]]:
        return [self.event_view(eid) for eid in self.events]

    # ------------------------------------------------------------------ #
    # Bets
    # ------------------------------------------------------------------ #
    def place_bet(
        self,
        event_id: str,
        bettor: str,
        selection: str,
        amount: float,
    ) -> Dict[str, Any]:
        event = self._event_or_raise(event_id)
        plugin = self._plugin_or_raise(event["type_id"])

        if not self.is_open_for_betting(event):
            raise BettingError(
                "Betting is closed for this event; the event has started or settled."
            )
        if amount <= 0:
            raise BettingError("Stake amount must be positive")
        if not plugin.validate_selection(selection, event["context"]):
            raise BettingError(f"Invalid selection '{selection}' for this event")

        odds = plugin.odds_for(selection, event["context"])
        bet_id = uuid.uuid4().hex
        placed_at = self._clock()
        transaction = {
            "type": "bet",
            "bet_id": bet_id,
            "event_id": event_id,
            "bettor": bettor,
            "selection": selection,
            "amount": float(amount),
            "odds": odds,
            "placed_at": placed_at,
        }
        block = self.chain.commit_transaction(transaction)

        bet = {
            "id": bet_id,
            "event_id": event_id,
            "bettor": bettor,
            "selection": selection,
            "amount": float(amount),
            "odds": odds,
            "placed_at": placed_at,
            "block_index": block.index,
            "block_hash": block.hash,
            "status": BET_ACTIVE,
            "payout": 0.0,
        }
        self.bets[bet_id] = bet
        return bet

    def list_bets(self, event_id: Optional[str] = None) -> List[Dict[str, Any]]:
        bets = list(self.bets.values())
        if event_id is not None:
            bets = [b for b in bets if b["event_id"] == event_id]
        return bets

    # ------------------------------------------------------------------ #
    # Settlement
    # ------------------------------------------------------------------ #
    def settle_event(self, event_id: str, outcome: str) -> Dict[str, Any]:
        event = self._event_or_raise(event_id)
        plugin = self._plugin_or_raise(event["type_id"])

        if event["status"] == EVENT_SETTLED:
            raise BettingError("Event is already settled")
        if not plugin.validate_selection(outcome, event["context"]):
            raise BettingError(f"Invalid outcome '{outcome}' for this event")

        event["status"] = EVENT_SETTLED
        event["outcome"] = outcome

        settled: List[Dict[str, Any]] = []
        for bet in self.bets.values():
            if bet["event_id"] != event_id or bet["status"] != BET_ACTIVE:
                continue
            won = plugin.is_winning(bet["selection"], outcome, event["context"])
            bet["status"] = BET_WON if won else BET_LOST
            bet["payout"] = round(bet["amount"] * bet["odds"], 2) if won else 0.0
            settled.append(bet)

        self.chain.commit_transaction(
            {
                "type": "settlement",
                "event_id": event_id,
                "outcome": outcome,
                "settled_at": self._clock(),
                "bet_results": [
                    {"bet_id": b["id"], "status": b["status"], "payout": b["payout"]}
                    for b in settled
                ],
            }
        )
        return self.event_view(event_id)

    # ------------------------------------------------------------------ #
    # Chain / integrity
    # ------------------------------------------------------------------ #
    def chain_status(self) -> Dict[str, Any]:
        return self.chain.to_dict()

    def verify_integrity(self) -> bool:
        return self.chain.is_valid()
