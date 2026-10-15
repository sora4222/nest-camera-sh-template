"""When reminders are due: `first_minutes` after the start, then 2x, 4x, 8x... that.

They stop after `max_minutes` from the start or `max_count` reminders, whichever is first.
"""

from datetime import datetime, timedelta


class Reminders:
    """A reminder schedule that gets further apart each time."""

    def __init__(self, first_minutes: float, max_minutes: float, max_count: int) -> None:
        """Not started, so nothing is due."""
        self._first = timedelta(minutes=first_minutes)
        self._max = timedelta(minutes=max_minutes)
        self._max_count = max_count
        self._since: datetime | None = None
        self._given = 0

    @property
    def active(self) -> bool:
        """Whether more reminders may still come."""
        return self._since is not None and self._next_at() is not None

    def start(self, at: datetime) -> None:
        """Start (or restart) the schedule from `at`."""
        self._since = at
        self._given = 0

    def stop(self) -> None:
        """No more reminders."""
        self._since = None

    def due(self, now: datetime) -> int | None:
        """The number (1, 2, ...) of the reminder due at `now`, or None.

        If several are overdue only the latest is given.
        """
        number = None
        while (at := self._next_at()) is not None and now >= at:
            self._given += 1
            number = self._given
        return number

    def _next_at(self) -> datetime | None:
        if self._since is None or self._given >= self._max_count:
            return None
        wait = self._first * 2**self._given
        return self._since + wait if wait <= self._max else None
