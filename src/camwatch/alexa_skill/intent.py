"""One Alexa intent: its name, what people say for it, and what it does."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from camwatch.alexa_skill.answers import Answer
from camwatch.alexa_skill.skill_context import SkillContext

type Handler = Callable[[SkillContext, Mapping[str, str]], Answer]
"""Gets the context and the slot values; gives the response."""


@dataclass(frozen=True)
class Intent:
    """An intent the skill answers.

    `make alexa-model` writes its samples and slots into the interaction model the Alexa
    developer console needs.
    """

    name: str
    handle: Handler
    samples: tuple[str, ...] = ()
    """What people say, with slots in braces: "quiet for {duration}"."""
    slots: Mapping[str, str] = field(default_factory=dict)
    """Slot name -> slot type, such as {"duration": "AMAZON.DURATION"}."""
