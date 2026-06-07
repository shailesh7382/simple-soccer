# ⚽ simple-soccer — Blockchain World Cup 2026 Betting Game

A full-stack betting game for the 2026 FIFA World Cup. Participants predict
tournament events at any point during the competition. Every bet is committed to
a **tamper-evident blockchain**, so the betting record's integrity cannot be
broken, and **betting automatically locks once an event starts** — you cannot
bet after the event. Game events (betting markets) are **pluggable**.

## Architecture

```
backend/   FastAPI + uvicorn API, custom proof-of-work blockchain, pluggable events
frontend/  React + Vite single-page app (events, betting, live chain explorer)
```

### How the blockchain guarantees integrity

* Each placed bet and each settlement is stored as a transaction inside a block.
* Blocks are linked by SHA-256 hashes and sealed with a proof-of-work nonce
  (`app/blockchain.py`).
* Modifying any historical bet changes its block hash, breaking every following
  block. `GET /api/chain` reports `valid: false` and the UI shows a tampered
  badge. See `tests/test_blockchain.py::test_tampering_is_detected`.

### Betting closes after the event

Every event has a `lock_time` (e.g. kickoff). `GameEngine.place_bet` rejects any
bet once `now >= lock_time` or after the event is settled, so bets can never be
placed after the event has happened.

### Pluggable game events

A betting market is an `EventPlugin` (`app/events/base.py`). Plugins live in
`app/events/plugins/` and self-register via the `@registry.register` decorator;
they are auto-discovered at startup. Bundled markets:

| Plugin          | Predicts                                |
| --------------- | --------------------------------------- |
| `match_winner`  | Home win / draw / away win              |
| `total_goals`   | Over / under a goals line               |
| `first_scorer`  | Which player scores first (dynamic)     |

**Add a new market** by dropping a new module into `app/events/plugins/` that
subclasses `EventPlugin` and applies `@registry.register`. No core changes
needed.

## Running the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://localhost:8000  (docs at /docs)
```

Run the tests:

```bash
cd backend && source .venv/bin/activate
python -m pytest
```

## Running the frontend

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173 (proxies /api -> :8000)
```

Build for production with `npm run build`.

## API overview

| Method & path                     | Purpose                                  |
| --------------------------------- | ---------------------------------------- |
| `GET  /api/health`                | Service status + chain validity          |
| `GET  /api/plugins`               | List available (pluggable) markets       |
| `GET  /api/events`                | List events with options & lock status   |
| `POST /api/events`                | Create an event                          |
| `POST /api/events/{id}/settle`    | Settle an event and pay out winners      |
| `GET  /api/bets[?event_id=]`      | List bets                                |
| `POST /api/bets`                  | Place a bet (rejected once locked)       |
| `GET  /api/chain`                 | Full blockchain + validity flag          |
