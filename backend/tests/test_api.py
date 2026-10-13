import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_plugins():
    assert client.get("/api/health").json()["status"] == "ok"
    plugins = client.get("/api/plugins").json()
    assert any(p["type_id"] == "match_winner" for p in plugins)


def test_full_betting_flow():
    created = client.post(
        "/api/events",
        json={
            "type_id": "match_winner",
            "title": "Argentina vs Spain",
            "context": {"home_team": "Argentina", "away_team": "Spain"},
            "lock_time": time.time() + 3600,
        },
    )
    assert created.status_code == 201
    event_id = created.json()["id"]

    bet = client.post(
        "/api/bets",
        json={
            "event_id": event_id,
            "bettor": "alice",
            "selection": "home",
            "amount": 25,
        },
    )
    assert bet.status_code == 201
    assert bet.json()["block_index"] >= 1

    chain = client.get("/api/chain").json()
    assert chain["valid"] is True

    settled = client.post(f"/api/events/{event_id}/settle", json={"outcome": "home"})
    assert settled.status_code == 200
    assert settled.json()["status"] == "settled"


def test_betting_after_lock_rejected():
    created = client.post(
        "/api/events",
        json={
            "type_id": "total_goals",
            "title": "Past match",
            "context": {"line": 2.5},
            "lock_time": time.time() - 10,  # already locked
        },
    )
    event_id = created.json()["id"]
    resp = client.post(
        "/api/bets",
        json={"event_id": event_id, "bettor": "bob", "selection": "over", "amount": 5},
    )
    assert resp.status_code == 400
