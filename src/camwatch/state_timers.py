"""Events that come from time spent in a State: `<state>_lasted` and `<state>_reminder`.

`[states.<name>] lasted_minutes` after entering the State, `<name>_lasted` is made once.
With `reminder_first_minutes`, `<name>_reminder` Events follow, further apart each time.
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from camwatch.config import StateSettings
from camwatch.domain import Event
from camwatch.reminders import Reminders


class StateTimers:
    """Watches how long the app has been in its current State."""

    def __init__(self, settings: Callable[[str], StateSettings]) -> None:
        """`settings` gives `[states.<name>]` for a State name."""
        self._settings = settings
        self._state = ""
        self._since: datetime | None = None
        self._lasted_said = False
        self._reminders: Reminders | None = None

    def enter(self, state: str, at: datetime) -> None:
        """The app entered `state` at `at`; start timing it."""
        self._state, self._since, self._lasted_said = state, at, False
        self._reminders = None

    def tick(self, now: datetime) -> list[Event]:
        """Events due at `now`."""
        if self._since is None:
            return []
        settings = self._settings(self._state)
        stayed = now - self._since
        minutes = f"{stayed.total_seconds() / 60:.0f}"
        events = []
        if (
            not self._lasted_said
            and settings.lasted_minutes is not None
            and stayed >= timedelta(minutes=settings.lasted_minutes)
        ):
            self._lasted_said = True
            events.append(
                Event(f"{self._state}_lasted", settings.urgency, now, {"minutes": minutes})
            )
            if settings.reminder_first_minutes is not None:
                self._reminders = Reminders(
                    settings.reminder_first_minutes,
                    settings.reminder_max_minutes,
                    settings.reminder_max_count,
                )
                self._reminders.start(now)
        if self._reminders is not None and (number := self._reminders.due(now)) is not None:
            details = {"minutes": minutes, "number": str(number)}
            events.append(Event(f"{self._state}_reminder", settings.urgency, now, details))
        return events
