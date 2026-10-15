"""The live watcher loop: read the camera, let the State machine act, pass on the Events.

Each check: States asked for by voice are moved to, State timer Events are made, and a
new Frame (if any) goes to the State machine. No picture for `offline_after` makes a
`camera_offline` Event; a refused camera login makes `login_expired`. Every Event goes in
the event log and then to the communications handler.
"""

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta

from camwatch.clock import Clock
from camwatch.config import ConfigError
from camwatch.domain import Event, Urgency
from camwatch.interfaces import CameraLoginExpired, CameraSource, CommunicationsHandler, EventLog
from camwatch.state_machine import StateMachine
from camwatch.state_requests import StateRequests

log = logging.getLogger(__name__)


class Watcher:
    """Checks the camera once per `step`; `run` steps every `check_seconds`."""

    def __init__(
        self,
        *,
        camera: CameraSource,
        machine: StateMachine,
        event_log: EventLog,
        communications: CommunicationsHandler,
        clock: Clock,
        offline_after: timedelta,
        check_seconds: float,
        requests: StateRequests | None = None,
    ) -> None:
        """`offline_after` with no picture is Camera Offline."""
        self._camera = camera
        self._machine = machine
        self._event_log = event_log
        self._communications = communications
        self._clock = clock
        self._offline_after = offline_after
        self._check_seconds = check_seconds
        self._requests = requests or StateRequests()
        self._last_picture = clock.now()
        self._offline_said = False
        self._login_said = False

    def run(self, stop: Callable[[], bool] = lambda: False) -> None:
        """Check every `check_seconds` until `stop()` is true."""
        while not stop():
            began = self._clock.now()
            self.step()
            used = (self._clock.now() - began).total_seconds()
            self._clock.sleep(max(0.0, self._check_seconds - used))

    def step(self) -> None:
        """Do one check (see the module docstring)."""
        now = self._clock.now()
        for name in self._requests.take():
            try:
                self._tell(self._machine.ask(name, now))
            except ConfigError as error:
                log.warning("cannot move to the State asked for: %s", error)
        self._tell(self._machine.tick(now))
        try:
            frame = self._camera.read()
        except CameraLoginExpired as error:
            frame = None
            if not self._login_said:
                log.error("camera login expired: %s", error)
                self._login_said = True
                self._tell([Event("login_expired", Urgency.NORMAL, now)])
        if frame is None:
            if not self._offline_said and now - self._last_picture >= self._offline_after:
                self._offline_said = True
                if not self._login_said:
                    self._tell([Event("camera_offline", Urgency.NORMAL, now)])
            return
        self._last_picture = now
        self._offline_said = self._login_said = False
        self._tell(self._machine.see(frame))

    def _tell(self, events: list[Event]) -> None:
        for event in events:
            if not event.state:
                event = replace(event, state=self._machine.state.name)
            self._event_log.record(event)
            try:
                self._communications.handle(event)
            except Exception:
                log.exception("the communications handler failed on %s", event.kind)
