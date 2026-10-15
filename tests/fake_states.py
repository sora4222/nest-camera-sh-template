"""Test-only States and a Model for them, so the machinery is tested without the example
States. Use the `test_states` fixture (conftest.py) to register them for one test."""

from datetime import datetime
from typing import ClassVar

import numpy as np
from pydantic import BaseModel

from camwatch.domain import Event, Frame, Urgency
from camwatch.model_output import ModelOutput
from camwatch.state import State, Transition


class Brightness(BaseModel):
    """What `FakeModel` gives back: how bright the Frame is, 0 to 1."""

    value: float


class FakeModel:
    """Gives the Frame's brightness; remembers how often it ran."""

    def __init__(self) -> None:
        self.runs = 0

    def run(self, frame: Frame, output: ModelOutput) -> Brightness:
        self.runs += 1
        return Brightness(value=float(np.asarray(frame.image).mean()) / 255)


class Dark(State):
    """Moves to `light` on a bright Frame."""

    name: ClassVar[str] = "dark"
    models: ClassVar[dict[str, int]] = {"bright": 1}

    def next(self, output: ModelOutput) -> Transition:
        seen = output.get("bright", Brightness)
        if seen is not None and seen.value > 0.5:
            return Transition(Light(), subject_action="lights on")
        return Transition(self)


class Light(State):
    """Checks every second Frame; counts dark ones; can be asked for by voice."""

    name: ClassVar[str] = "light"
    models: ClassVar[dict[str, int]] = {"bright": 2}
    voice_names: ClassVar[tuple[str, ...]] = ("lights on",)

    dark_frames: int = 0

    def next(self, output: ModelOutput) -> Transition:
        seen = output.get("bright", Brightness)
        if seen is None:
            return Transition(self)
        self.dark_frames = self.dark_frames + 1 if seen.value <= 0.5 else 0
        if self.dark_frames >= 2:
            return Transition(Dark(), subject_action="lights off")
        extra = [Event("flicker", Urgency.INFO, output.at)] if seen.value > 0.9 else []
        return Transition(self, extra, subject_action="reading")


TEST_STATES = {"dark": Dark, "light": Light}


def frame(at: datetime, value: int) -> Frame:
    return Frame(at, np.full((4, 4, 3), value, np.uint8))
