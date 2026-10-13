import pytest


@pytest.fixture(autouse=True)
def _discover_plugins():
    from app.events.base import registry

    registry.discover()
