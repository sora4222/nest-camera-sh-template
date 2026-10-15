from collections.abc import Mapping
from typing import Any

import pytest

from camwatch.config import Config, ConfigError
from camwatch.domain import Presence
from camwatch.registry import (
    CAMERA,
    COMMUNICATIONS,
    EVENT_LOG,
    MODEL,
    PRESENCE,
    STATE_STORE,
    Registry,
    UnknownPart,
    build_models,
    build_parts,
    default_registry,
)


class FakePresence:
    def __init__(self, presence: Presence) -> None:
        self.presence = presence

    def check(self, listener: str) -> Presence:
        return self.presence


def make_config(**changes: Any) -> Config:
    data: dict[str, Any] = {
        "app": {"start_state": "no_one_at_desk"},
        "parts": dict.fromkeys(
            ["camera", "event_log", "state_store", "presence", "communications"], "fake"
        ),
        "paths": {"private_data": "/data"},
    }
    data.update(changes)
    return Config.model_validate(data)


def made_as(kind: str):
    """A factory that gives back its kind and options, to check what was made."""
    return lambda config, options: (kind, dict(options))


def fake_registry() -> Registry:
    registry = Registry()
    for slot in [CAMERA, EVENT_LOG, STATE_STORE, COMMUNICATIONS]:
        registry.add(slot, "fake", made_as(slot.kind))  # type: ignore[arg-type]
    registry.add(PRESENCE, "fake", lambda config, options: FakePresence(Presence.HOME))
    registry.add(MODEL, "model_y", lambda config, options: ("model_y", dict(options)))
    return registry


def test_create_uses_registered_factory_with_part_options():
    registry = Registry()
    seen: list[Mapping[str, Any]] = []

    def factory(config: Config, options: Mapping[str, Any]) -> FakePresence:
        seen.append(options)
        return FakePresence(Presence.AWAY)

    registry.add(PRESENCE, "wifi", factory)
    config = make_config(presence={"timeout_minutes": 10})
    part = registry.create(PRESENCE, "wifi", config, config.part_options("presence"))
    assert part.check("Me") is Presence.AWAY
    assert seen == [{"timeout_minutes": 10}]


def test_unknown_name_lists_known_names():
    registry = Registry()
    registry.add(PRESENCE, "off", lambda config, options: FakePresence(Presence.UNKNOWN))
    with pytest.raises(UnknownPart, match=r"'wifi'.*off"):
        registry.create(PRESENCE, "wifi", make_config(), {})


def test_unknown_part_is_a_config_error():
    assert issubclass(UnknownPart, ConfigError)


def test_same_name_twice_is_refused():
    registry = Registry()
    registry.add(PRESENCE, "off", lambda config, options: FakePresence(Presence.UNKNOWN))
    with pytest.raises(ValueError, match="off"):
        registry.add(PRESENCE, "off", lambda config, options: FakePresence(Presence.UNKNOWN))


def test_decorator_registers_factory():
    registry = Registry()

    @registry.part(PRESENCE, "home")
    def _home(config: Config, options: Mapping[str, Any]) -> FakePresence:
        return FakePresence(Presence.HOME)

    assert registry.names(PRESENCE) == ["home"]


def test_build_parts_makes_every_part_with_its_options():
    parts = build_parts(make_config(camera={"file": "a.mp4"}), fake_registry())
    assert parts.camera == ("camera", {"file": "a.mp4"})
    assert parts.state_store == ("state_store", {})


def test_models_are_made_by_name_with_their_own_options():
    config = make_config(models={"model_y": {"file": "y.onnx"}})
    assert build_models(config, fake_registry(), ["model_y"]) == {
        "model_y": ("model_y", {"file": "y.onnx"})
    }


def test_an_unknown_model_is_a_config_error():
    with pytest.raises(UnknownPart, match="model_z"):
        build_models(make_config(), fake_registry(), ["model_z"])


def test_the_default_registry_has_the_built_in_parts_and_model_x():
    registry = default_registry()
    assert "model_x" in registry.names(MODEL)
    assert {"nest", "video_file"} <= set(registry.names(CAMERA))
    assert {"memory", "postgres"} <= set(registry.names(STATE_STORE))
