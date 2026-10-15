"""Alexa response envelopes and request slots."""

from typing import Any

type Answer = dict[str, Any]


def say(text: str, *, listen: str | None = None, remember: dict[str, str] | None = None) -> Answer:
    """A response that says `text`; with `listen`, the session stays open and reprompts.

    `remember` is kept in the session, so the next request can use it.
    """
    response: dict[str, Any] = {
        "outputSpeech": {"type": "PlainText", "text": text},
        "shouldEndSession": listen is None,
    }
    if listen is not None:
        response["reprompt"] = {"outputSpeech": {"type": "PlainText", "text": listen}}
    answer: Answer = {"version": "1.0", "response": response}
    if remember:
        answer["sessionAttributes"] = remember
    return answer


def slots(intent: dict[str, Any]) -> dict[str, str]:
    """Slot name -> value, for slots that have a value."""
    found = intent.get("slots") or {}
    return {
        name: slot["value"]
        for name, slot in found.items()
        if isinstance(slot, dict) and isinstance(slot.get("value"), str)
    }
