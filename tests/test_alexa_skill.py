from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fake_clock import FakeClock

from camwatch.alexa_skill.answers import say
from camwatch.alexa_skill.intent import Intent
from camwatch.alexa_skill.skill import AlexaSkill, all_intents
from camwatch.alexa_skill.skill_context import SkillContext
from camwatch.communications.switches import Switches
from camwatch.domain import Event, Urgency
from camwatch.parts.memory_event_log import MemoryEventLog
from camwatch.state_requests import StateRequests

NOW = datetime(2026, 10, 11, 14, 0, tzinfo=UTC)


@dataclass
class Status:
    state_name: str = "person_at_desk"
    since: datetime = NOW - timedelta(hours=1)
    subject_action: str | None = "at the desk"


@pytest.fixture
def context(tmp_path) -> SkillContext:
    return SkillContext(
        clock=FakeClock(NOW),
        zone=ZoneInfo("UTC"),
        switches=Switches(tmp_path / "switches.json"),
        requests=StateRequests(),
        event_log=MemoryEventLog(),
        status=Status(),
        voice_states={"on a break": "on_break", "back at work": "no_one_at_desk"},
    )


@pytest.fixture
def skill(context) -> AlexaSkill:
    return AlexaSkill(context)


def intent(name: str, session: dict | None = None, **slots: str) -> dict:
    request = {
        "version": "1.0",
        "request": {
            "type": "IntentRequest",
            "intent": {
                "name": name,
                "slots": {key: {"name": key, "value": value} for key, value in slots.items()},
            },
        },
    }
    if session is not None:
        request["session"] = {"attributes": session}
    return request


def speech(answer: dict) -> str:
    return answer["response"]["outputSpeech"]["text"]


def ends(answer: dict) -> bool:
    return answer["response"]["shouldEndSession"]


def test_launch_says_what_it_can_do_and_listens(skill):
    answer = skill.respond({"request": {"type": "LaunchRequest"}})
    assert "what's happening" in speech(answer)
    assert not ends(answer)


def test_status_says_the_state_since_when_and_the_subject_action(skill):
    assert speech(skill.respond(intent("StatusIntent"))) == (
        "Person at desk since 1 PM. Last seen: at the desk."
    )


def test_status_mentions_do_not_disturb(skill, context):
    context.switches.set_do_not_disturb(NOW + timedelta(hours=2))
    assert "Do Not Disturb is on until 4 PM." in speech(skill.respond(intent("StatusIntent")))


def test_a_voice_name_asks_the_watcher_to_move_to_its_state(skill, context):
    answer = skill.respond(intent("SetStateIntent", state="On a Break"))
    assert speech(answer) == "OK, on a break."
    assert context.requests.take() == ["on_break"]


def test_an_unknown_voice_name_lists_what_can_be_said(skill, context):
    answer = skill.respond(intent("SetStateIntent", state="asleep"))
    assert speech(answer) == "Sorry, I can't do that. You can say: back at work, on a break."
    assert context.requests.take() == []


def test_do_not_disturb_for_a_while_and_off(skill, context):
    assert speech(skill.respond(intent("DoNotDisturbIntent", duration="PT2H"))) == (
        "OK, Do Not Disturb until 4 PM."
    )
    assert context.switches.do_not_disturb(NOW).until == NOW + timedelta(hours=2)
    assert speech(skill.respond(intent("StopDoNotDisturbIntent"))) == "OK, Do Not Disturb is off."
    assert speech(skill.respond(intent("StopDoNotDisturbIntent"))) == "Do Not Disturb was not on."


def test_do_not_disturb_with_no_duration_asks_how_long_and_remembers(skill, context):
    answer = skill.respond(intent("DoNotDisturbIntent"))
    assert "how long" in speech(answer).lower() and not ends(answer)
    skill.respond(intent("DurationIntent", answer["sessionAttributes"], duration="PT1H"))
    assert context.switches.do_not_disturb(NOW).until == NOW + timedelta(hours=1)


@pytest.mark.parametrize("value", ["soon", "P2W"])
def test_a_duration_it_cannot_use_asks_again(skill, context, value):
    answer = skill.respond(intent("DoNotDisturbIntent", duration=value))
    assert not ends(answer)
    assert context.switches.do_not_disturb(NOW) is None


def test_a_bare_duration_without_a_question_gets_help(skill, context):
    answer = skill.respond(intent("DurationIntent", duration="PT2H"))
    assert "You can ask" in speech(answer)
    assert context.switches.do_not_disturb(NOW) is None


def test_the_example_custom_intent_says_the_newest_event(skill, context):
    assert speech(skill.respond(intent("LastEventIntent"))) == "Nothing has happened yet."
    context.event_log.record(Event("on_break_entered", Urgency.NORMAL, NOW))
    assert speech(skill.respond(intent("LastEventIntent"))) == "On break entered at 2 PM."


@pytest.mark.parametrize("name", ["AMAZON.HelpIntent", "AMAZON.FallbackIntent", "Nonsense"])
def test_help_fallback_and_unknown_intents_listen(skill, name):
    assert not ends(skill.respond(intent(name)))


@pytest.mark.parametrize("name", ["AMAZON.StopIntent", "AMAZON.CancelIntent"])
def test_stop_and_cancel_end_the_session(skill, name):
    assert speech(skill.respond(intent(name))) == "Bye."


def test_session_ended_gets_an_empty_response(skill):
    assert skill.respond({"request": {"type": "SessionEndedRequest"}}) == {
        "version": "1.0",
        "response": {},
    }


def test_a_custom_intent_with_a_built_in_name_replaces_it(context):
    mine = Intent("StatusIntent", lambda context, slots: say("Mine."))
    skill = AlexaSkill(context, all_intents() | {"StatusIntent": mine})
    assert speech(skill.respond(intent("StatusIntent"))) == "Mine."
