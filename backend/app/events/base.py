"""Pluggable game-event (betting market) system.

A *game event* is a market participants can bet on (e.g. "who wins this match",
"total goals", "first scorer"). Each event type is implemented as an
:class:`EventPlugin`. Plugins are registered in the :data:`registry` and are
auto-discovered from :mod:`app.events.plugins`, so new markets can be added by
dropping a new module into that package without touching the core engine.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type


class EventPlugin:
    """Base class for a pluggable betting market.

    Subclasses describe a *kind* of bettable event. Concrete events (a specific
    match, a specific final) are created from a plugin via :meth:`create_event`.
    """

    #: Unique machine identifier for the plugin, e.g. ``"match_winner"``.
    type_id: str = ""
    #: Human readable name shown in the UI.
    display_name: str = ""
    #: Short description of what is being predicted.
    description: str = ""

    def options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the selectable outcomes for an event of this type.

        Each option is a dict with at least ``id`` and ``label`` keys and an
        optional ``odds`` multiplier (defaults to ``2.0``).

        Args:
            context: Event-specific data (teams, players, etc.).
        """
        raise NotImplementedError

    def validate_selection(self, selection: str, context: Dict[str, Any]) -> bool:
        """Return ``True`` if ``selection`` is a valid outcome id for the event."""
        return any(opt["id"] == selection for opt in self.options(context))

    def odds_for(self, selection: str, context: Dict[str, Any]) -> float:
        """Return the payout multiplier for a winning ``selection``."""
        for opt in self.options(context):
            if opt["id"] == selection:
                return float(opt.get("odds", 2.0))
        return 1.0

    def is_winning(self, selection: str, outcome: str, context: Dict[str, Any]) -> bool:
        """Return ``True`` if ``selection`` wins given the settled ``outcome``."""
        return selection == outcome

    def describe(self) -> Dict[str, Any]:
        return {
            "type_id": self.type_id,
            "display_name": self.display_name,
            "description": self.description,
        }


class PluginRegistry:
    """Holds the set of available :class:`EventPlugin` instances."""

    def __init__(self) -> None:
        self._plugins: Dict[str, EventPlugin] = {}

    def register(self, plugin_cls: Type[EventPlugin]) -> Type[EventPlugin]:
        """Register a plugin class. Usable as a decorator."""
        instance = plugin_cls()
        if not instance.type_id:
            raise ValueError(f"{plugin_cls.__name__} must define a type_id")
        self._plugins[instance.type_id] = instance
        return plugin_cls

    def get(self, type_id: str) -> Optional[EventPlugin]:
        return self._plugins.get(type_id)

    def all(self) -> List[EventPlugin]:
        return list(self._plugins.values())

    def discover(self, package: str = "app.events.plugins") -> None:
        """Import every module in ``package`` so its plugins self-register."""
        pkg = importlib.import_module(package)
        for mod in pkgutil.iter_modules(pkg.__path__):
            importlib.import_module(f"{package}.{mod.name}")


#: Global registry used by the application.
registry = PluginRegistry()
