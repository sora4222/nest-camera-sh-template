from datetime import UTC, datetime

import pytest
from fake_states import Brightness, FakeModel, frame

from camwatch.model_runner import ModelRunner

AT = datetime(2026, 1, 1, tzinfo=UTC)


class Broken:
    def run(self, frame, output):
        raise RuntimeError("model file is bad")


class ReadsEarlier:
    """Model Y: doubles what the bright Model gave on the same Frame."""

    def run(self, frame, output):
        earlier = output.get("bright", Brightness)
        return Brightness(value=0 if earlier is None else earlier.value * 2)


def test_each_model_runs_on_every_nth_frame():
    bright = FakeModel()
    runner = ModelRunner({"bright": bright})
    ran = [runner.run(frame(AT, 255), n, {"bright": 3}).names() for n in range(1, 7)]
    assert ran == [[], [], ["bright"], [], [], ["bright"]]
    assert bright.runs == 2


def test_later_models_read_what_earlier_ones_gave():
    runner = ModelRunner({"bright": FakeModel(), "y": ReadsEarlier()})
    output = runner.run(frame(AT, 51), 1, {"bright": 1, "y": 1})
    assert output.get("y", Brightness) == Brightness(value=0.4)


def test_a_failing_model_is_logged_and_left_out(caplog):
    runner = ModelRunner({"broken": Broken(), "bright": FakeModel()})
    output = runner.run(frame(AT, 0), 1, {"broken": 1, "bright": 1})
    assert output.names() == ["bright"]
    assert "broken" in caplog.text


def test_a_model_that_was_never_made_is_an_error():
    with pytest.raises(KeyError, match="model_z"):
        ModelRunner({}).run(frame(AT, 0), 1, {"model_z": 1})
