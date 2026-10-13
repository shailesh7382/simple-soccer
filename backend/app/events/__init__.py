"""Pluggable event system package."""

from app.events.base import EventPlugin, PluginRegistry, registry

__all__ = ["EventPlugin", "PluginRegistry", "registry"]
