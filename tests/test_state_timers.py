from datetime import UTC, datetime, timedelta

from camwatch.config import StateSettings
from camwatch.domain import Urgency
from camwatch.state_timers import StateTimers

START = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
SETTINGS = {
    "desk": StateSettings(
        urgency=Urgency.URGENT,
        lasted_minutes=50,
        reminder_first_minutes=5,
        reminder_max_minutes=20,
    ),
    "break": StateSettings(lasted_minutes=10),
}


def timers() -> StateTimers:
    timers = StateTimers(lambda name: SETTINGS.get(name, StateSettings()))
    timers.enter("desk", START)
    return timers


def kinds(timers: StateTimers, minutes: float) -> list[str]:
    return [e.kind for e in timers.tick(START + timedelta(minutes=minutes))]


def test_lasted_comes_once_after_lasted_minutes():
    t = timers()
    assert kinds(t, 49) == []
    [lasted] = t.tick(START + timedelta(minutes=50))
    assert (lasted.kind, lasted.urgency, lasted.details) == (
        "desk_lasted",
        Urgency.URGENT,
        {"minutes": "50"},
    )
    assert kinds(t, 51) == []


def test_reminders_follow_further_apart_each_time_and_stop():
    t = timers()
    kinds(t, 50)
    reminders = [m for m in range(51, 200) if kinds(t, m)]
    assert reminders == [55, 60, 70]  # 5, 10 and 20 minutes after; 40 is over the max


def test_entering_another_state_starts_again():
    t = timers()
    t.enter("break", START + timedelta(minutes=30))
    assert kinds(t, 39) == []
    assert kinds(t, 40) == ["break_lasted"]


def test_a_state_with_no_settings_makes_nothing():
    t = StateTimers(lambda name: StateSettings())
    t.enter("other", START)
    assert t.tick(START + timedelta(days=1)) == []
