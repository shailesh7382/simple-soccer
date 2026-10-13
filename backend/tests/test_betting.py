import pytest

from app.betting import BettingError, GameEngine


class FakeClock:
    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now


@pytest.fixture
def engine():
    from app.events.base import registry

    registry.discover()
    clock = FakeClock()
    eng = GameEngine(difficulty=2, clock=clock)
    eng._test_clock = clock  # type: ignore[attr-defined]
    return eng


def _make_match(engine, lock_time=2000.0):
    return engine.create_event(
        type_id="match_winner",
        title="Brazil vs France",
        context={"home_team": "Brazil", "away_team": "France"},
        lock_time=lock_time,
    )


def test_place_bet_commits_to_chain(engine):
    event = _make_match(engine)
    bet = engine.place_bet(event["id"], "alice", "home", 50)
    assert bet["status"] == "active"
    assert bet["block_index"] >= 1
    assert bet["odds"] == 2.4
    assert engine.verify_integrity()
    # The bet is recorded as a transaction on the chain.
    txs = engine.chain.find_transactions(type="bet", bet_id=bet["id"])
    assert len(txs) == 1


def test_betting_locked_after_lock_time(engine):
    event = _make_match(engine, lock_time=1500.0)
    engine._test_clock.now = 1600.0  # event has started
    with pytest.raises(BettingError):
        engine.place_bet(event["id"], "bob", "away", 10)


def test_betting_locked_when_settled(engine):
    event = _make_match(engine)
    engine.settle_event(event["id"], "home")
    with pytest.raises(BettingError):
        engine.place_bet(event["id"], "carol", "home", 10)


def test_invalid_selection_rejected(engine):
    event = _make_match(engine)
    with pytest.raises(BettingError):
        engine.place_bet(event["id"], "dave", "moon", 10)


def test_settlement_computes_payouts(engine):
    event = _make_match(engine)
    winner = engine.place_bet(event["id"], "alice", "home", 100)
    loser = engine.place_bet(event["id"], "bob", "away", 100)
    engine.settle_event(event["id"], "home")
    assert engine.bets[winner["id"]]["status"] == "won"
    assert engine.bets[winner["id"]]["payout"] == pytest.approx(240.0)
    assert engine.bets[loser["id"]]["status"] == "lost"
    assert engine.bets[loser["id"]]["payout"] == 0.0
    assert engine.verify_integrity()


def test_open_for_betting_flag_in_view(engine):
    event = _make_match(engine, lock_time=1500.0)
    assert engine.event_view(event["id"])["open_for_betting"] is True
    engine._test_clock.now = 1600.0
    view = engine.event_view(event["id"])
    assert view["open_for_betting"] is False
    assert view["status"] == "locked"


def test_double_settle_rejected(engine):
    event = _make_match(engine)
    engine.settle_event(event["id"], "home")
    with pytest.raises(BettingError):
        engine.settle_event(event["id"], "away")
