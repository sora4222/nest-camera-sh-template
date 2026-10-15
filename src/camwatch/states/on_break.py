"""Example State: on a break, set by voice ("Alexa, tell camera watch I'm on a break").

No Models run here. `[states.on_break] lasted_minutes` says when the break is over.

TODO(template): replace the example States with your own, one State per file.
"""

from typing import ClassVar

from camwatch.model_output import ModelOutput
from camwatch.state import State, Transition
from camwatch.state_registry import register_state


@register_state
class OnBreak(State):
    """Stay here until someone says they are back."""

    name: ClassVar[str] = "on_break"
    voice_names: ClassVar[tuple[str, ...]] = ("on a break", "taking a break")

    def next(self, output: ModelOutput) -> Transition:
        """Stay; only a voice command leaves this State."""
        return Transition(self, subject_action="on a break")
