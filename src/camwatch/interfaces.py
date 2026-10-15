"""Small interfaces for the swappable parts. Implementations are chosen in config.

Each part is registered by name in `camwatch.registry`. Tests use fakes, never real
cameras, speakers or the network.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel

from camwatch.domain import Event, Frame, Presence
from camwatch.model_output import ModelOutput


class CameraLoginExpired(Exception):
    """The camera service refused the login; a person must log in again."""


class CameraSource(Protocol):
    """Gives pictures from the camera."""

    def read(self) -> Frame | None:
        """The next new Frame, or None if there is no new picture right now.

        Raises `CameraLoginExpired` while the camera cannot be reached without a new login.
        """
        ...


class Model(Protocol):
    """Reads a Frame and gives values back (Model X, Model Y...). One folder per Model."""

    def run(self, frame: Frame, output: ModelOutput) -> BaseModel:
        """This Model's output for `frame`; `output` holds what earlier Models gave."""
        ...


class EventLog(Protocol):
    """Keeps every Event."""

    def record(self, event: Event) -> None:
        """Store `event`."""
        ...

    def recent(self, limit: int) -> list[Event]:
        """Up to `limit` Events, newest first."""
        ...


@dataclass(frozen=True)
class SavedState:
    """A State as saved: its name, its fields as JSON, and when it was entered."""

    name: str
    data: str
    since: datetime


class StateStore(Protocol):
    """Keeps the current State, so the app goes back to it after a restart."""

    def save(self, state: SavedState) -> None:
        """Remember `state` as the current State."""
        ...

    def last(self) -> SavedState | None:
        """The last saved State, or None if none was saved."""
        ...


class PresenceCheck(Protocol):
    """Says whether a Listener is home."""

    def check(self, listener: str) -> Presence:
        """Presence of the Listener named `listener` in config."""
        ...


class Speaker(Protocol):
    """A device that says a message out loud."""

    name: str

    def say(self, text: str) -> None:
        """Say `text` now."""
        ...


class SpeechMaker(Protocol):
    """Turns text into speech on this machine (Piper)."""

    def wav(self, text: str) -> bytes:
        """`text` spoken, as the bytes of a wav file."""
        ...


class AudioHost(Protocol):
    """Makes audio reachable by speakers on the home network."""

    def offer(self, wav: bytes) -> str:
        """The URL `wav` can be fetched from for a while."""
        ...


class AudioPlayer(Protocol):
    """One network speaker that plays audio from a URL (a Google speaker)."""

    def play(self, url: str) -> None:
        """Start playing `url`."""
        ...


class ServiceManager(Protocol):
    """The user's systemd (`systemctl --user`), for installing the watcher service."""

    def reload(self) -> None:
        """Read unit files again after one was added, changed or removed."""
        ...

    def enable_and_restart(self, unit: str) -> None:
        """Start `unit` at every start of the user's systemd, and (re)start it now."""
        ...

    def disable_now(self, unit: str) -> None:
        """Stop `unit` now and no longer start it."""
        ...


class CertificateSource(Protocol):
    """Fetches the certificate chain Alexa signs skill requests with (from Amazon's S3)."""

    def fetch(self, url: str) -> bytes:
        """The PEM chain at `url`; raises OSError (or a subclass) if it cannot be fetched."""
        ...


class CommunicationsHandler(Protocol):
    """The one gate every Announcement goes through (Quiet Hours, presence, Speakers)."""

    def handle(self, event: Event) -> None:
        """Log `event`; announce it if it is not log only and the rules allow it."""
        ...
