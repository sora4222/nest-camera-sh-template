from datetime import UTC, datetime, timedelta

import pytest
from fake_clock import FakeClock
from fake_states import FakeModel, frame

from camwatch.config import ConfigError, StateSettings
from camwatch.domain import Event, Frame
from camwatch.interfaces import CameraLoginExpired
from camwatch.model_runner import ModelRunner
from camwatch.parts.memory_event_log import MemoryEventLog
from camwatch.parts.memory_state_store import MemoryStateStore
from camwatch.state_machine import StateMachine
from camwatch.state_requests import StateRequests
from camwatch.watcher.watcher import Watcher

START = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)

pytestmark = pytest.mark.usefixtures("test_states")


class ScriptedCamera:
    """One character per read: `#` a bright Frame, `.` a dark one, `-` no picture,
    `L` Login Expired."""

    def __init__(self, script: str, clock: FakeClock) -> None:
        self._script = iter(script)
        self._clock = clock

    def read(self) -> Frame | None:
        step = next(self._script)
        if step == "L":
            raise CameraLoginExpired("refused")
        if step == "-":
            return None
        return frame(self._clock.now(), 255 if step == "#" else 0)


class Heard:
    def __init__(self, fails: bool = False) -> None:
        self.events: list[Event] = []
        self.fails = fails

    def handle(self, event: Event) -> None:
        self.events.append(event)
        if self.fails:
            raise RuntimeError("speaker gone")


class Setup:
    def __init__(self, script: str, settings: dict | None = None, fails: bool = False) -> None:
        self.clock = FakeClock(START)
        self.log = MemoryEventLog()
        self.heard = Heard(fails)
        self.requests = StateRequests()
        self.machine = StateMachine.resume(
            start_name="dark",
            now=START,
            store=MemoryStateStore(),
            runner=ModelRunner({"bright": FakeModel()}),
            settings=lambda name: (settings or {}).get(name, StateSettings()),
        )
        self.watcher = Watcher(
            camera=ScriptedCamera(script, self.clock),
            machine=self.machine,
            event_log=self.log,
            communications=self.heard,
            clock=self.clock,
            offline_after=timedelta(minutes=10),
            check_seconds=60,
            requests=self.requests,
        )
        self.steps = len(script)

    def run(self) -> list[str]:
        steps = iter(range(self.steps))
        self.watcher.run(stop=lambda: next(steps, None) is None)
        return [event.kind for event in self.log.recent(100)][::-1]


def test_frames_go_to_the_state_machine_and_events_to_log_and_communications():
    setup = Setup("..#")
    assert setup.run() == ["dark_left", "light_entered"]
    assert [e.kind for e in setup.heard.events] == ["dark_left", "light_entered"]
    assert setup.machine.state_name == "light"


def test_no_picture_for_long_enough_is_camera_offline_once():
    setup = Setup("-" * 12)
    assert setup.run() == ["camera_offline"]
    [offline] = setup.log.recent(1)
    assert offline.state == "dark"


def test_a_picture_again_resets_camera_offline():
    assert Setup("-" * 11 + "." + "-" * 11).run() == ["camera_offline", "camera_offline"]


def test_login_expired_is_said_once_and_hides_camera_offline():
    assert Setup("L" * 12).run() == ["login_expired"]


def test_states_asked_for_move_the_app_on_the_next_check():
    setup = Setup("..")
    setup.requests.ask("light")
    setup.requests.ask("nowhere")
    assert setup.run() == ["dark_left", "light_entered"]


def test_state_timers_are_checked_every_step():
    setup = Setup("#" + "-" * 3, settings={"light": StateSettings(lasted_minutes=2)})
    assert setup.run() == ["dark_left", "light_entered", "light_lasted"]


def test_a_failing_communications_handler_does_not_stop_the_watcher(caplog):
    setup = Setup(".#", fails=True)
    assert setup.run() == ["dark_left", "light_entered"]
    assert "communications handler failed" in caplog.text


def test_run_waits_check_seconds_less_the_time_used():
    setup = Setup("...")
    setup.run()
    assert setup.clock.slept == [60, 60, 60]


def test_unknown_requested_state_is_logged(caplog):
    setup = Setup(".")
    setup.requests.ask("nowhere")
    setup.run()
    assert "nowhere" in caplog.text
    with pytest.raises(ConfigError):
        setup.machine.ask("nowhere", START)
