import pytest

from camwatch.config import Config, ConfigError
from camwatch.parts.alexa_speaker import AlexaSpeaker, NoSensor
from camwatch.registry import SPEAKER, default_registry

TEMPLATES = {"desk_entered": "{subject} sat down.", "on_break_lasted": "Break over!"}


class Gateway:
    def __init__(self) -> None:
        self.fired: list[str] = []

    def trigger(self, endpoint_id: str) -> None:
        self.fired.append(endpoint_id)


def speaker(gateway: Gateway) -> AlexaSpeaker:
    return AlexaSpeaker("Echo", TEMPLATES, {"subject": "Sam"}, gateway)


def test_say_fires_the_sensor_of_the_message_kind():
    gateway = Gateway()
    speaker(gateway).say("Break over!")
    assert gateway.fired == ["camwatch-on-break-lasted"]


def test_text_from_no_template_raises():
    with pytest.raises(NoSensor):
        speaker(Gateway()).say("hello")


def config() -> Config:
    return Config.model_validate(
        {
            "app": {"start_state": "no_one_at_desk"},
            "paths": {"private_data": "/data"},
            "messages": TEMPLATES,
        }
    )


def test_registered_as_alexa(monkeypatch):
    monkeypatch.setenv("CAMWATCH_ALEXA_CLIENT_ID", "id")
    monkeypatch.setenv("CAMWATCH_ALEXA_CLIENT_SECRET", "secret")
    options = {"name": "Echo", "kind": "alexa", "region": "FE"}
    part = default_registry().create(SPEAKER, "alexa", config(), options)
    assert isinstance(part, AlexaSpeaker)


def test_unknown_region_is_a_config_error():
    options = {"name": "Echo", "kind": "alexa", "region": "AU"}
    with pytest.raises(ConfigError, match="region"):
        default_registry().create(SPEAKER, "alexa", config(), options)
