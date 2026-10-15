"""What the skill says and does for each Alexa request (already verified).

Intents are the built-in ones (`built_in_intents.py`) and the app's own
(`custom_intents.py`); `make alexa-model` writes them all into
`alexa/interactionModels/custom/en-US.json`.
"""

from typing import Any

from camwatch.alexa_skill.answers import Answer, say, slots
from camwatch.alexa_skill.built_in_intents import ASKED_FOR, BUILT_IN_INTENTS, HELP, REPROMPT
from camwatch.alexa_skill.custom_intents import CUSTOM_INTENTS
from camwatch.alexa_skill.intent import Intent
from camwatch.alexa_skill.skill_context import SkillContext


def all_intents() -> dict[str, Intent]:
    """Every intent by name; a custom intent with a built-in's name replaces it."""
    return {intent.name: intent for intent in (*BUILT_IN_INTENTS, *CUSTOM_INTENTS)}


class AlexaSkill:
    """Answers Alexa requests with the intents in `intents`."""

    def __init__(self, context: SkillContext, intents: dict[str, Intent] | None = None) -> None:
        """Answer with `context`; `intents` defaults to `all_intents()`."""
        self._context = context
        self._intents = all_intents() if intents is None else intents

    def respond(self, request: dict[str, Any]) -> Answer:
        """The response envelope for one Alexa request."""
        inner = request.get("request") or {}
        kind = inner.get("type")
        if kind == "LaunchRequest":
            return say("Hello. " + HELP, listen=REPROMPT)
        if kind != "IntentRequest":
            return {"version": "1.0", "response": {}}  # SessionEndedRequest and the like
        intent = inner.get("intent") or {}
        name = intent.get("name", "")
        if name == "DurationIntent":  # the answer to "for how long?"
            attributes = (request.get("session") or {}).get("attributes") or {}
            name = attributes.get(ASKED_FOR, name)
        found = self._intents.get(name) or self._intents["AMAZON.HelpIntent"]
        return found.handle(self._context, slots(intent))
