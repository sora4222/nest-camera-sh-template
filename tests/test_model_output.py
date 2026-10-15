from datetime import UTC, datetime

import pytest
from fake_states import Brightness, frame
from pydantic import BaseModel

from camwatch.model_output import ModelOutput

AT = datetime(2026, 1, 1, tzinfo=UTC)


class Other(BaseModel):
    text: str


def test_outputs_are_kept_by_model_name_in_the_order_they_ran():
    output = ModelOutput(frame(AT, 0))
    output.add("model_y", Other(text="hi"))
    output.add("model_x", Brightness(value=0.5))
    assert output.names() == ["model_y", "model_x"]
    assert output.get("model_x", Brightness) == Brightness(value=0.5)
    assert output.at == AT


def test_a_model_that_did_not_run_gives_none():
    assert ModelOutput(frame(AT, 0)).get("model_x", Brightness) is None


def test_asking_for_the_wrong_schema_is_an_error():
    output = ModelOutput(frame(AT, 0))
    output.add("model_x", Other(text="hi"))
    with pytest.raises(TypeError, match="model_x"):
        output.get("model_x", Brightness)


def test_json_for_the_event_log():
    output = ModelOutput(frame(AT, 0))
    output.add("model_x", Brightness(value=0.25))
    assert output.to_json() == {"model_x": {"value": 0.25}}
