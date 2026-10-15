"""The intents every app gets: status, move to a State, Do Not Disturb, help and stop."""

from collections.abc import Mapping
from datetime import timedelta

from camwatch.alexa_skill.answers import Answer, say
from camwatch.alexa_skill.durations import parse_alexa_duration
from camwatch.alexa_skill.intent import Intent
from camwatch.alexa_skill.skill_context import SkillContext
from camwatch.alexa_skill.spoken_time import spoken_time

MAX_QUIET = timedelta(weeks=1)
STATE_SLOT_TYPE = "STATE_NAME"
"""The custom slot type whose values are every State's `voice_names`."""
HELP = (
    "You can ask: what's happening? Or say: do not disturb for two hours, "
    "or tell me which state to move to. What would you like?"
)
REPROMPT = "What would you like? For example: what's happening?"
HOW_LONG = "For how long? For example: two hours."
ASKED_FOR = "asked_for"
"""Session key: what the last answer asked "for how long?" about."""


def _words(name: str) -> str:
    return name.replace("_", " ")


def status(context: SkillContext, slots: Mapping[str, str]) -> Answer:
    """The current State, since when, the Subject Action and Do Not Disturb."""
    now = context.clock.now()
    app = context.status
    when = spoken_time(app.since, now, context.zone)
    parts = [f"{_words(app.state_name).capitalize()} since {when}."]
    if app.subject_action:
        parts.append(f"Last seen: {app.subject_action}.")
    dnd = context.switches.do_not_disturb(now)
    if dnd is not None:
        parts.append(f"Do Not Disturb is on until {spoken_time(dnd.until, now, context.zone)}.")
    return say(" ".join(parts))


def set_state(context: SkillContext, slots: Mapping[str, str]) -> Answer:
    """Ask the watcher to move to the State whose voice name was said."""
    said = slots.get("state", "").strip().lower()
    name = context.voice_states.get(said)
    if name is None:
        choices = ", ".join(sorted(context.voice_states)) or "none"
        return say(f"Sorry, I can't do that. You can say: {choices}.")
    context.requests.ask(name)
    return say(f"OK, {said}.")


def do_not_disturb(context: SkillContext, slots: Mapping[str, str]) -> Answer:
    """Turn Do Not Disturb on for the duration said, asking for one if there is none."""
    ask = {ASKED_FOR: "DoNotDisturbIntent"}
    value = slots.get("duration")
    if not value:
        return say(HOW_LONG, listen=HOW_LONG, remember=ask)
    try:
        span = parse_alexa_duration(value)
    except ValueError:
        return say("Sorry, I didn't get how long. " + HOW_LONG, listen=HOW_LONG, remember=ask)
    if span > MAX_QUIET:
        return say("I can be quiet for up to a week. " + HOW_LONG, listen=HOW_LONG, remember=ask)
    now = context.clock.now()
    context.switches.set_do_not_disturb(now + span)
    return say(f"OK, Do Not Disturb until {spoken_time(now + span, now, context.zone)}.")


def stop_do_not_disturb(context: SkillContext, slots: Mapping[str, str]) -> Answer:
    """Turn Do Not Disturb off."""
    was_on = context.switches.do_not_disturb(context.clock.now()) is not None
    context.switches.clear_do_not_disturb()
    return say("OK, Do Not Disturb is off." if was_on else "Do Not Disturb was not on.")


def help_answer(context: SkillContext, slots: Mapping[str, str]) -> Answer:
    """What the skill can do; the session stays open."""
    return say(HELP, listen=REPROMPT)


def goodbye(context: SkillContext, slots: Mapping[str, str]) -> Answer:
    """End the session."""
    return say("Bye.")


BUILT_IN_INTENTS = (
    Intent(
        "StatusIntent",
        status,
        ("what's happening", "what is happening", "status", "what's going on", "how is it going"),
    ),
    Intent(
        "SetStateIntent",
        set_state,
        ("i'm {state}", "i am {state}", "we're {state}", "move to {state}"),
        {"state": STATE_SLOT_TYPE},
    ),
    Intent(
        "DoNotDisturbIntent",
        do_not_disturb,
        ("do not disturb for {duration}", "be quiet for {duration}", "do not disturb"),
        {"duration": "AMAZON.DURATION"},
    ),
    Intent(
        "DurationIntent",  # the answer to "for how long?" (see AlexaSkill.respond)
        help_answer,
        ("{duration}",),
        {"duration": "AMAZON.DURATION"},
    ),
    Intent(
        "StopDoNotDisturbIntent",
        stop_do_not_disturb,
        ("stop do not disturb", "turn off do not disturb", "you can talk again"),
    ),
    Intent("AMAZON.HelpIntent", help_answer),
    Intent("AMAZON.FallbackIntent", help_answer),
    Intent("AMAZON.NavigateHomeIntent", help_answer),
    Intent("AMAZON.StopIntent", goodbye),
    Intent("AMAZON.CancelIntent", goodbye),
)
