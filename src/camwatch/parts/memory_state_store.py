"""State store "memory": the State is forgotten on restart. For tests and trying things out."""

from collections.abc import Mapping
from typing import Any

from camwatch.config import Config
from camwatch.interfaces import SavedState
from camwatch.registry import DEFAULT, STATE_STORE


class MemoryStateStore:
    """Keeps the last saved State."""

    def __init__(self) -> None:
        """Nothing saved yet."""
        self._last: SavedState | None = None

    def save(self, state: SavedState) -> None:
        """Remember `state` as the current State."""
        self._last = state

    def last(self) -> SavedState | None:
        """The last saved State, or None."""
        return self._last


@DEFAULT.part(STATE_STORE, "memory")
def _create(config: Config, options: Mapping[str, Any]) -> MemoryStateStore:
    return MemoryStateStore()
