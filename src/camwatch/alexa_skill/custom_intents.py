"""Your app's own Alexa intents. Add one `Intent` per command to `CUSTOM_INTENTS`.

TODO(template): replace the example with your own intents. For each one:
1. Write a handler: it gets the `SkillContext` and the slot values, and returns `say(...)`.
   To change the State, call `context.requests.ask("<state name>")`; never change it here.
2. Add an `Intent(name, handler, samples, slots)` to `CUSTOM_INTENTS`.
3. Run `make alexa-model` and paste the file into the Alexa developer console.
See docs/alexa.md.
"""

from collections.abc import Mapping

from camwatch.alexa_skill.answers import Answer, say
from camwatch.alexa_skill.intent import Intent
from camwatch.alexa_skill.skill_context import SkillContext
from camwatch.alexa_skill.spoken_time import spoken_time


def last_event(context: SkillContext, slots: Mapping[str, str]) -> Answer:
    """Example: say the newest Event in the event log and when it happened."""
    newest = context.event_log.recent(1)
    if not newest:
        return say("Nothing has happened yet.")
    event = newest[0]
    when = spoken_time(event.at, context.clock.now(), context.zone)
    return say(f"{event.kind.replace('_', ' ').capitalize()} at {when}.")


CUSTOM_INTENTS: tuple[Intent, ...] = (
    Intent("LastEventIntent", last_event, ("what happened last", "what was the last thing")),
)
