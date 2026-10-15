"""Shared words from GLOSSARY.md as types, passed between the swappable parts."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Urgency(StrEnum):
    """How important an Announcement is. Never spoken aloud."""

    INFO = "info"
    NORMAL = "normal"
    URGENT = "urgent"


class Presence(StrEnum):
    """Whether a Listener is at home. Unknown counts as Away."""

    HOME = "home"
    AWAY = "away"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Frame:
    """One picture from the camera. `image` is an RGB array (height, width, 3)."""

    taken_at: datetime
    image: Any


@dataclass(frozen=True)
class Event:
    """Something worth logging and maybe announcing, such as a State being entered."""

    kind: str
    urgency: Urgency
    at: datetime
    details: dict[str, str] = field(default_factory=dict)
    announce: bool = True
    """False for Events that only go in the event log."""
    state: str = ""
    """The State the app was in when the Event happened."""
    subject_action: str | None = None
    """What the Subject was doing, if the State knows."""
    model_output: dict[str, Any] = field(default_factory=dict)
    """The Model Output of the Frame that caused the Event, as JSON values."""
