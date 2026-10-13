"""Total-goals market: predict whether total goals are over/under a line."""

from __future__ import annotations

from typing import Any, Dict, List

from app.events.base import EventPlugin, registry


@registry.register
class TotalGoalsPlugin(EventPlugin):
    type_id = "total_goals"
    display_name = "Total Goals"
    description = "Predict whether the combined goal count is over or under the line."

    def options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        line = context.get("line", 2.5)
        return [
            {"id": "over", "label": f"Over {line}", "odds": 1.9},
            {"id": "under", "label": f"Under {line}", "odds": 1.9},
        ]
