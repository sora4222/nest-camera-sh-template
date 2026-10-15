from datetime import UTC, datetime

import pytest

from camwatch.communications.messages import message_text
from camwatch.domain import Event, Urgency

AT = datetime(2026, 6, 1, 20, 0, tzinfo=UTC)
NAMES = {"subject": "Sam"}


def test_text_comes_from_the_template_for_the_event_kind_with_names_and_details():
    templates = {"desk_lasted": "{subject} has been at the desk for {minutes} minutes."}
    event = Event("desk_lasted", Urgency.INFO, AT, {"minutes": "50"})
    assert message_text(templates, NAMES, event) == "Sam has been at the desk for 50 minutes."


def test_the_subject_action_can_be_said():
    templates = {"desk_entered": "{subject} is {subject_action}."}
    event = Event("desk_entered", Urgency.INFO, AT, subject_action="sitting down")
    assert message_text(templates, NAMES, event) == "Sam is sitting down."


def test_no_template_means_nothing_to_say():
    assert message_text({}, NAMES, Event("desk_entered", Urgency.NORMAL, AT)) is None


def test_a_template_naming_a_missing_detail_says_nothing_and_logs_why(caplog):
    templates = {"desk_reminder": "Reminder number {number}."}
    assert message_text(templates, NAMES, Event("desk_reminder", Urgency.NORMAL, AT)) is None
    assert "number" in caplog.text


@pytest.mark.parametrize(
    "template", ["{subject.name} is here.", "{subject[9]} is here.", "{subject[x]} is here."]
)
def test_a_template_reaching_into_something_it_cannot_says_nothing(template):
    event = Event("desk_entered", Urgency.NORMAL, AT)
    assert message_text({"desk_entered": template}, NAMES, event) is None
