"""Example State: no one is at the desk. The app starts here (`[app] start_state`).

TODO(template): replace the example States with your own, one State per file.
"""

from typing import ClassVar

from camwatch.model_output import ModelOutput
from camwatch.models.model_x.model_x_schema import ModelXOutput
from camwatch.state import State, Transition
from camwatch.state_registry import register_state, state_class

SEEN_FRAMES = 4
"""A person must be in this many Frames in a row before they count as at the desk."""


@register_state
class NoOneAtDesk(State):
    """Watch for a person with Model X on every second Frame."""

    name: ClassVar[str] = "no_one_at_desk"
    models: ClassVar[dict[str, int]] = {"model_x": 2}
    voice_names: ClassVar[tuple[str, ...]] = ("back at work", "watching")

    seen: int = 0
    """Frames in a row with a person in them."""

    def next(self, output: ModelOutput) -> Transition:
        """Move to `person_at_desk` once a person stays in view."""
        found = output.get("model_x", ModelXOutput)
        if found is None:  # Model X did not run on this Frame
            return Transition(self)
        self.seen = self.seen + 1 if found.has("person") else 0
        if self.seen >= SEEN_FRAMES:
            return Transition(state_class("person_at_desk")(), subject_action="sitting down")
        return Transition(self, subject_action="away from the desk")
