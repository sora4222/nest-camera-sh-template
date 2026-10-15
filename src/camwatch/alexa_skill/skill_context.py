"""What an intent handler can read and change."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from camwatch.clock import Clock
from camwatch.communications.switches import Switches
from camwatch.interfaces import EventLog
from camwatch.state_requests import StateRequests


class AppStatus(Protocol):
    """The app's State right now (the State machine)."""

    @property
    def state_name(self) -> str:
        """The current State's name."""
        ...

    @property
    def since(self) -> datetime:
        """When the current State was entered."""
        ...

    @property
    def subject_action(self) -> str | None:
        """What the Subject is doing, if known."""
        ...


@dataclass(frozen=True)
class SkillContext:
    """Everything a handler needs.

    Handlers never change the State themselves: they ask for it with `requests`, and the
    watcher moves on its next check.
    """

    clock: Clock
    zone: ZoneInfo
    """The camera's time zone; times are said in it."""
    switches: Switches
    requests: StateRequests
    event_log: EventLog
    status: AppStatus
    voice_states: dict[str, str]
    """What people may say -> the State name it moves to (from each State's `voice_names`)."""
