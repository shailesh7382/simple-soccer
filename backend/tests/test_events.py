from app.events.base import registry


def test_plugins_discovered():
    registry.discover()
    type_ids = {p.type_id for p in registry.all()}
    assert {"match_winner", "total_goals", "first_scorer"} <= type_ids


def test_match_winner_options():
    registry.discover()
    plugin = registry.get("match_winner")
    opts = plugin.options({"home_team": "Brazil", "away_team": "France"})
    ids = {o["id"] for o in opts}
    assert ids == {"home", "draw", "away"}
    assert plugin.validate_selection("home", {})
    assert not plugin.validate_selection("nope", {})
    assert plugin.odds_for("draw", {}) == 3.1


def test_first_scorer_dynamic_options():
    registry.discover()
    plugin = registry.get("first_scorer")
    ctx = {"players": ["Messi", "Mbappe"], "odds": {"Messi": 4.0}}
    opts = plugin.options(ctx)
    ids = {o["id"] for o in opts}
    assert ids == {"Messi", "Mbappe", "no_scorer"}
    assert plugin.odds_for("Messi", ctx) == 4.0


def test_total_goals_options():
    registry.discover()
    plugin = registry.get("total_goals")
    opts = plugin.options({"line": 3.5})
    assert {o["id"] for o in opts} == {"over", "under"}
    assert "3.5" in opts[0]["label"]
