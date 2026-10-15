import socket
import time
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fake_clock import FakeClock
from fake_states import FakeModel, frame

from camwatch.cli import main
from camwatch.config import Config, ConfigError
from camwatch.domain import Event, Frame
from camwatch.interfaces import SavedState
from camwatch.parts.memory_event_log import MemoryEventLog
from camwatch.parts.memory_state_store import MemoryStateStore
from camwatch.registry import CAMERA, COMMUNICATIONS, EVENT_LOG, MODEL, STATE_STORE, Registry
from camwatch.watcher.command import start_watcher, used_models
from camwatch.watcher_lock import WatcherLock

START = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)

pytestmark = pytest.mark.usefixtures("test_states")


class Lamp:
    """A camera that shows a bright Frame each time."""

    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self.reads = 0

    def read(self) -> Frame:
        self.reads += 1
        return frame(self.clock.now(), 255)


class Heard:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


def setup(tmp_path, store=None):
    clock = FakeClock(START)
    camera = Lamp(clock)
    heard = Heard()
    registry = Registry()
    registry.add(CAMERA, "fake", lambda config, options: camera)
    registry.add(EVENT_LOG, "fake", lambda config, options: MemoryEventLog())
    registry.add(STATE_STORE, "fake", lambda config, options: store or MemoryStateStore())
    registry.add(COMMUNICATIONS, "fake", lambda config, options: heard)
    registry.add(MODEL, "bright", lambda config, options: FakeModel())
    config = Config.model_validate(
        {
            "app": {"start_state": "dark"},
            "parts": dict.fromkeys(
                ["camera", "event_log", "state_store", "communications"], "fake"
            ),
            "paths": {
                "private_data": str(tmp_path / "store"),
                "lock_file": str(tmp_path / "lock" / "watcher.lock"),
            },
            "watcher": {"check_seconds": 0.5},
        }
    )
    return config, registry, clock, camera, heard


def stop_after(checks: int):
    left = iter(range(checks))
    return lambda: next(left, None) is None


def test_watcher_runs_until_stopped_and_the_states_act(tmp_path):
    config, registry, clock, camera, heard = setup(tmp_path)
    assert start_watcher(config, registry, clock, stop_after(3)) == 0
    assert camera.reads == 3
    assert clock.slept == [0.5, 0.5, 0.5]
    assert [e.kind for e in heard.events] == ["dark_left", "light_entered", "flicker"]


def test_only_the_models_some_state_runs_are_made():
    assert used_models() == ["bright"]


def test_it_starts_in_the_state_saved_before_a_restart(tmp_path):
    store = MemoryStateStore()
    store.save(SavedState("light", "{}", START - timedelta(hours=1)))
    config, registry, clock, _, heard = setup(tmp_path, store)
    assert start_watcher(config, registry, clock, stop_after(1)) == 0
    assert heard.events == []  # no move: already in light


def test_a_second_watcher_refuses_to_start(tmp_path, capsys):
    config, registry, clock, camera, _ = setup(tmp_path)
    lock_file = config.paths.lock_file
    assert lock_file is not None
    with WatcherLock(lock_file):
        assert start_watcher(config, registry, clock, stop_after(3)) == 1
    assert camera.reads == 0
    assert "already" in capsys.readouterr().err


def test_watch_reports_a_missing_config(tmp_path, capsys):
    assert main(["watch", "--config", str(tmp_path / "missing.toml")]) == 1
    assert "not found" in capsys.readouterr().err


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def with_skill(config: Config, port: int) -> Config:
    skill = config.alexa_skill.model_copy(update={"enabled": True, "port": port})
    return config.model_copy(update={"alexa_skill": skill})


def test_the_alexa_skill_is_served_while_the_watcher_runs(tmp_path):
    config, registry, clock, _, _ = setup(tmp_path)
    port = free_port()
    statuses = []

    def stop() -> bool:
        with httpx.Client(trust_env=False) as client:
            try:
                statuses.append(client.get(f"http://127.0.0.1:{port}/alexa").status_code)
            except httpx.ConnectError:
                time.sleep(0.01)
        return len(statuses) >= 2

    environ = {"CAMWATCH_ALEXA_SKILL_ID": "amzn1.ask.skill.test"}
    assert start_watcher(with_skill(config, port), registry, clock, stop, environ) == 0
    assert statuses == [405, 405]


def test_an_enabled_alexa_skill_without_its_id_stops_the_watcher(tmp_path):
    config, registry, clock, camera, _ = setup(tmp_path)
    with pytest.raises(ConfigError, match="CAMWATCH_ALEXA_SKILL_ID"):
        start_watcher(with_skill(config, free_port()), registry, clock, stop_after(3), {})
    assert camera.reads == 0
