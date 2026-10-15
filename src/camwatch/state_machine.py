"""The State machine: run the current State's Models on each Frame and move between States.

Moving from one State to another makes a `<old>_left` and a `<new>_entered` Event, saves
the new State in the State store, and restarts the State timers. At startup the last
saved State is picked up again (`resume`).
"""

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from pydantic import ValidationError

from camwatch.config import ConfigError, StateSettings
from camwatch.domain import Event, Frame
from camwatch.interfaces import SavedState, StateStore
from camwatch.model_output import ModelOutput
from camwatch.model_runner import ModelRunner
from camwatch.state import State
from camwatch.state_registry import state_class
from camwatch.state_timers import StateTimers

log = logging.getLogger(__name__)


class StateMachine:
    """Holds the current State and the Subject Action."""

    def __init__(
        self,
        *,
        start: State,
        since: datetime,
        store: StateStore,
        runner: ModelRunner,
        settings: Callable[[str], StateSettings],
    ) -> None:
        """Start in `start`, entered at `since` (already saved in `store`)."""
        self.state = start
        self.since = since
        self.subject_action: str | None = None
        self._store = store
        self._runner = runner
        self._settings = settings
        self._timers = StateTimers(settings)
        self._timers.enter(start.name, since)
        self._frames = 0

    @classmethod
    def resume(
        cls,
        *,
        start_name: str,
        now: datetime,
        store: StateStore,
        runner: ModelRunner,
        settings: Callable[[str], StateSettings],
    ) -> "StateMachine":
        """Start in the last saved State, or in `start_name` if there is none (or it broke)."""
        saved = store.last()
        start, since = None, now
        if saved is not None:
            try:
                start = state_class(saved.name).model_validate_json(saved.data)
                since = saved.since
                log.info("back in State %s, entered at %s", saved.name, since.isoformat())
            except (ValidationError, ConfigError) as error:
                log.warning("cannot go back to saved State %s: %s", saved.name, error)
        if start is None:
            start = state_class(start_name)()
            store.save(SavedState(start.name, start.model_dump_json(), now))
        return cls(start=start, since=since, store=store, runner=runner, settings=settings)

    @property
    def state_name(self) -> str:
        """The current State's name."""
        return self.state.name

    def see(self, frame: Frame) -> list[Event]:
        """Run the current State's Models on `frame` and act on what it decides."""
        self._frames += 1
        output = self._runner.run(frame, self._frames, self.state.wanted_models())
        transition = self.state.next(output)
        if transition.subject_action is not None:
            self.subject_action = transition.subject_action
        events = [self._stamp(e, output) for e in transition.events]
        if transition.state is not self.state:
            events += self.move_to(transition.state, output.at, output)
        return events

    def move_to(self, new: State, at: datetime, output: ModelOutput | None = None) -> list[Event]:
        """Leave the current State for `new` at `at`; nothing happens if it is the same one."""
        old = self.state
        self.state = new
        if new.name == old.name:
            return []
        self.since = at
        self._store.save(SavedState(new.name, new.model_dump_json(), at))
        self._timers.enter(new.name, at)
        details = {"from": old.name, "to": new.name}
        urgency = self._settings
        left = Event(f"{old.name}_left", urgency(old.name).urgency, at, details, state=old.name)
        entered = Event(
            f"{new.name}_entered", urgency(new.name).urgency, at, details, state=new.name
        )
        return [self._stamp(left, output), self._stamp(entered, output)]

    def ask(self, name: str, at: datetime) -> list[Event]:
        """Move to the State registered as `name` (asked by a person, such as through Alexa)."""
        return self.move_to(state_class(name)(), at)

    def tick(self, now: datetime) -> list[Event]:
        """Events due from time spent in the current State."""
        return [self._stamp(event, None) for event in self._timers.tick(now)]

    def _stamp(self, event: Event, output: ModelOutput | None) -> Event:
        """`event` with the State, the Subject Action and the Model Output filled in."""
        return replace(
            event,
            state=event.state or self.state.name,
            subject_action=event.subject_action or self.subject_action,
            model_output=event.model_output or (output.to_json() if output else {}),
        )
