"""Example State: a person is at the desk.

`[states.person_at_desk]` sets when to remind them to take a break.

TODO(template): replace the example States with your own, one State per file.
"""

from typing import ClassVar

from camwatch.model_output import ModelOutput
from camwatch.models.model_x.model_x_schema import ModelXOutput
from camwatch.state import State, Transition
from camwatch.state_registry import register_state, state_class

GONE_FRAMES = 20
"""No person for this many checked Frames in a row means they left."""


@register_state
class PersonAtDesk(State):
    """Check with Model X every fourth Frame that the person is still there."""

    name: ClassVar[str] = "person_at_desk"
    models: ClassVar[dict[str, int]] = {"model_x": 4}

    missing: int = 0
    """Checked Frames in a row with no person in them."""

    def next(self, output: ModelOutput) -> Transition:
        """Move to `no_one_at_desk` once the person has gone."""
        found = output.get("model_x", ModelXOutput)
        if found is None:
            return Transition(self)
        self.missing = 0 if found.has("person") else self.missing + 1
        if self.missing >= GONE_FRAMES:
            return Transition(state_class("no_one_at_desk")(), subject_action="left the desk")
        return Transition(self, subject_action="at the desk")
