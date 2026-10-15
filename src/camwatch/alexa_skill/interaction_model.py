"""The Alexa interaction model, which `make alexa-model` writes for the developer console.

It holds the invocation name, every intent's samples and slots, and the State names
people may say.
"""

from collections.abc import Iterable
from typing import Any

from camwatch.alexa_skill.built_in_intents import STATE_SLOT_TYPE
from camwatch.alexa_skill.intent import Intent

_REQUIRED_BUILT_INS = ("AMAZON.HelpIntent", "AMAZON.StopIntent", "AMAZON.CancelIntent")


def interaction_model(
    invocation: str, intents: Iterable[Intent], voice_names: Iterable[str]
) -> dict[str, Any]:
    """The model as JSON values for `en-US.json`."""
    out = []
    for intent in intents:
        entry: dict[str, Any] = {"name": intent.name, "samples": list(intent.samples)}
        if intent.slots:
            entry["slots"] = [{"name": n, "type": t} for n, t in intent.slots.items()]
        out.append(entry)
    names = {entry["name"] for entry in out}
    out += [{"name": name, "samples": []} for name in _REQUIRED_BUILT_INS if name not in names]
    values = [{"name": {"value": name}} for name in sorted(set(voice_names))]
    return {
        "interactionModel": {
            "languageModel": {
                "invocationName": invocation.lower(),
                "intents": out,
                "types": [
                    {"name": STATE_SLOT_TYPE, "values": values or [{"name": {"value": "none"}}]}
                ],
            }
        }
    }
