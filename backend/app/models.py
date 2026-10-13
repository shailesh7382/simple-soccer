"""Pydantic request/response models for the betting API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    type_id: str = Field(..., description="Plugin type id, e.g. 'match_winner'.")
    title: str = Field(..., description="Human readable event title.")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Plugin-specific data (teams, players, line, ...).",
    )
    lock_time: float = Field(
        ...,
        description="Unix timestamp after which betting is closed (e.g. kickoff).",
    )


class EventOption(BaseModel):
    id: str
    label: str
    odds: float = 2.0


class EventOut(BaseModel):
    id: str
    type_id: str
    title: str
    context: Dict[str, Any]
    lock_time: float
    status: str
    outcome: Optional[str] = None
    options: List[EventOption]
    open_for_betting: bool


class BetCreate(BaseModel):
    event_id: str
    bettor: str = Field(..., description="Participant name or wallet id.")
    selection: str = Field(..., description="Chosen outcome option id.")
    amount: float = Field(..., gt=0, description="Stake amount (must be > 0).")


class BetOut(BaseModel):
    id: str
    event_id: str
    bettor: str
    selection: str
    amount: float
    odds: float
    placed_at: float
    block_index: int
    block_hash: str
    status: str
    payout: float = 0.0


class SettleRequest(BaseModel):
    outcome: str = Field(..., description="The winning option id for the event.")
