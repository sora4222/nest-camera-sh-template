import logging
from datetime import UTC, datetime

from camwatch.domain import Event, Presence, Urgency
from camwatch.parts.log_speaker import LogSpeaker
from camwatch.parts.memory_event_log import MemoryEventLog
from camwatch.parts.presence_off import PresenceOff
from camwatch.registry import EVENT_LOG, PRESENCE, SPEAKER, default_registry


def event(minute: int) -> Event:
    return Event("desk_entered", Urgency.NORMAL, datetime(2026, 1, 1, 8, minute, tzinfo=UTC))


def test_memory_event_log_returns_newest_first():
    log = MemoryEventLog()
    for minute in range(3):
        log.record(event(minute))
    assert log.recent(2) == [event(2), event(1)]


def test_presence_off_is_always_unknown():
    assert PresenceOff().check("Partner") is Presence.UNKNOWN


def test_log_speaker_writes_text_to_the_log(caplog):
    with caplog.at_level(logging.INFO):
        LogSpeaker("Kitchen").say("hello")
    assert "Kitchen: hello" in caplog.text


def test_default_registry_has_the_builtin_parts():
    registry = default_registry()
    assert "memory" in registry.names(EVENT_LOG)
    assert "off" in registry.names(PRESENCE)
    assert "log" in registry.names(SPEAKER)
