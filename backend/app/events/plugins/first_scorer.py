"""First-scorer market: predict which player scores first.

Demonstrates a dynamic, context-driven option set: the available outcomes are
built from the ``players`` list supplied when the event is created.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.events.base import EventPlugin, registry


@registry.register
class FirstScorerPlugin(EventPlugin):
    type_id = "first_scorer"
    display_name = "First Goal Scorer"
    description = "Predict which player scores the first goal of the match."

    def options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        players: List[str] = context.get("players", [])
        opts = [
            {"id": player, "label": player, "odds": float(context.get("odds", {}).get(player, 6.0))}
            for player in players
        ]
        opts.append({"id": "no_scorer", "label": "No goal scored", "odds": 9.0})
        return opts
