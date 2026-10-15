from datetime import UTC, datetime

from camwatch.domain import Event, Urgency


def test_events_are_announced_unless_they_are_only_for_the_log():
    at = datetime(2026, 1, 1, tzinfo=UTC)
    assert Event("door_opened", Urgency.NORMAL, at).announce
    assert not Event("door_seen", Urgency.INFO, at, announce=False).announce


def test_events_start_with_no_state_subject_action_or_model_output():
    event = Event("door_opened", Urgency.NORMAL, datetime(2026, 1, 1, tzinfo=UTC))
    assert (event.state, event.subject_action, event.model_output) == ("", None, {})
