"""FastAPI application exposing the blockchain betting game.

Run with uvicorn::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.betting import BettingError, GameEngine
from app.events.base import registry
from app.models import (
    BetCreate,
    BetOut,
    EventCreate,
    EventOut,
    SettleRequest,
)

# Discover bundled event plugins so their markets are available.
registry.discover()

app = FastAPI(
    title="Soccer World Cup 2026 Blockchain Betting Game",
    description=(
        "Predict tournament events at any point. Every bet is committed to a "
        "tamper-evident blockchain and betting locks automatically once an "
        "event starts."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = GameEngine()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "chain_valid": engine.verify_integrity()}


@app.get("/api/plugins")
def list_plugins() -> list:
    """List the available (pluggable) event market types."""
    return [p.describe() for p in registry.all()]


@app.get("/api/events", response_model=List[EventOut])
def list_events() -> list:
    return engine.list_events()


@app.post("/api/events", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate) -> dict:
    try:
        return engine.create_event(
            type_id=payload.type_id,
            title=payload.title,
            context=payload.context,
            lock_time=payload.lock_time,
        )
    except BettingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/events/{event_id}", response_model=EventOut)
def get_event(event_id: str) -> dict:
    try:
        return engine.event_view(event_id)
    except BettingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/events/{event_id}/settle", response_model=EventOut)
def settle_event(event_id: str, payload: SettleRequest) -> dict:
    try:
        return engine.settle_event(event_id, payload.outcome)
    except BettingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/bets", response_model=List[BetOut])
def list_bets(event_id: str | None = None) -> list:
    return engine.list_bets(event_id)


@app.post("/api/bets", response_model=BetOut, status_code=201)
def place_bet(payload: BetCreate) -> dict:
    try:
        return engine.place_bet(
            event_id=payload.event_id,
            bettor=payload.bettor,
            selection=payload.selection,
            amount=payload.amount,
        )
    except BettingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/chain")
def get_chain() -> dict:
    """Return the full chain plus its validity flag."""
    return engine.chain_status()
