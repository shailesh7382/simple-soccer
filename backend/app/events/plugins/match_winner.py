"""Match-winner market: predict the home win, away win, or a draw."""

from __future__ import annotations

from typing import Any, Dict, List

from app.events.base import EventPlugin, registry


@registry.register
class MatchWinnerPlugin(EventPlugin):
    type_id = "match_winner"
    display_name = "Match Winner"
    description = "Predict which team wins the match (or a draw)."

    def options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        home = context.get("home_team", "Home")
        away = context.get("away_team", "Away")
        return [
            {"id": "home", "label": f"{home} win", "odds": 2.4},
            {"id": "draw", "label": "Draw", "odds": 3.1},
            {"id": "away", "label": f"{away} win", "odds": 2.6},
        ]
