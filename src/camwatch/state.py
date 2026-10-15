"""The State base class: the condition the app is in, and what runs next.

Each State lives in its own file in `camwatch/states/`. A State says which Models run
while the app is in it (`models`), and `next` reads the Model Output of each Frame and
says which State comes next, with any Events and the Subject Action.

A State is a Pydantic model: its fields are what it remembers between Frames (such as
how many Frames in a row showed a person). The State is saved each time it changes, and
the app goes back to it after a restart.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar

from pydantic import BaseModel

from camwatch.domain import Event
from camwatch.model_output import ModelOutput


class State(BaseModel):
    """One condition the app can be in. Subclass it in its own file in `camwatch/states/`."""

    name: ClassVar[str]
    """Unique name, used in config (`[states.<name>]`), messages and the database."""

    models: ClassVar[Mapping[str, int]] = {}
    """Model name -> `every_frame`: run that Model on every Nth Frame while in this State.
    Models run in this order."""

    voice_names: ClassVar[tuple[str, ...]] = ()
    """What people may say to the Alexa skill to move the app to this State, such as
    ("on a break",). Empty: Alexa cannot move the app here."""

    def wanted_models(self) -> Mapping[str, int]:
        """The Models to run now; `models` unless a State overrides this."""
        return self.models

    def next(self, output: ModelOutput) -> "Transition":
        """What happens after the Models ran on one Frame. Override in every State."""
        raise NotImplementedError(f"{type(self).__name__}.next")


@dataclass
class Transition:
    """What a State decided after one Frame."""

    state: State
    """The next State; the same object to stay."""
    events: list[Event] = field(default_factory=list)
    """Extra Events to log (and maybe say), besides the automatic State Events."""
    subject_action: str | None = None
    """What the Subject is doing, such as "at the desk", if this State knows."""
