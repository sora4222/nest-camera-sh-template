from datetime import UTC, datetime

from camwatch.interfaces import SavedState
from camwatch.parts.memory_state_store import MemoryStateStore


def test_keeps_only_the_last_saved_state():
    store = MemoryStateStore()
    assert store.last() is None
    at = datetime(2026, 1, 1, tzinfo=UTC)
    store.save(SavedState("a", "{}", at))
    store.save(SavedState("b", "{}", at))
    assert store.last() == SavedState("b", "{}", at)
