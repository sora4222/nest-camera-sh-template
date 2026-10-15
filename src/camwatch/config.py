"""Load and check the private config file (`config.toml`, never committed).

The path is `$CAMWATCH_CONFIG` if set, else `config.toml` in the current folder.
See `config.example.toml` for every setting.
"""

import os
import tomllib
from datetime import time
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from camwatch.domain import Urgency

PartKind = Literal["camera", "event_log", "state_store", "presence", "communications"]
Weekday = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class ConfigError(Exception):
    """The config file is missing or has a wrong value."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _Open(BaseModel):
    """A table that also holds plug-in specific keys."""

    model_config = ConfigDict(extra="allow", frozen=True)


class PartChoices(_Strict):
    """Which implementation to use for each swappable part, by registered name."""

    camera: str = "video_file"
    event_log: str = "memory"
    state_store: str = "memory"
    presence: str = "off"
    communications: str = "standard"


class AppSettings(_Strict):
    """The app itself."""

    start_state: str
    """The State the app starts in when no State was saved."""
    timezone: str = "UTC"
    """IANA time zone of the camera, e.g. `Australia/Melbourne`; Quiet Hours and spoken
    times are read in it."""

    @field_validator("timezone")
    @classmethod
    def _known_zone(cls, name: str) -> str:
        try:
            ZoneInfo(name)
        except (ValueError, KeyError, OSError):  # ZoneInfoNotFoundError is a KeyError
            raise ValueError(f"unknown time zone {name!r}") from None
        return name


class Paths(_Strict):
    """Where things live outside the repo."""

    private_data: Path = Path.home() / ".local/share/camwatch"
    """Model files, clips and labels. Can be a folder on a NAS."""
    lock_file: Path | None = None  # None: `watcher_lock.default_lock_path()`

    def private(self, path: Path | str) -> Path:
        """`path`, inside `private_data` when it is relative."""
        return self.private_data / Path(path)


class ListenerSettings(_Open):
    """A person who may hear Announcements. Presence options are plug-in specific."""

    name: str


class SpeakerSettings(_Open):
    """A device that can say a message. `kind` picks the speaker plug-in."""

    name: str
    kind: str


class QuietHours(_Strict):
    """A repeating quiet time. `allow` lists the Urgencies that may still be spoken."""

    days: list[Weekday]
    start: time
    end: time
    allow: list[Urgency] = []


class StateSettings(_Strict):
    """How one State is announced (`[states.<name>]`).

    Each Event is only said if `[messages]` has a template for it.
    """

    urgency: Urgency = Urgency.NORMAL
    lasted_minutes: float | None = Field(None, gt=0)
    """Make `<name>_lasted` once the app has been in this State this long."""
    reminder_first_minutes: float | None = Field(None, gt=0)
    """After `<name>_lasted`, make `<name>_reminder` this long after, then 2x, 4x... that."""
    reminder_max_minutes: float = Field(60, gt=0)
    reminder_max_count: int = Field(6, ge=0)


class WatcherSettings(_Strict):
    """How often the live watcher checks the camera (`make dev`)."""

    check_seconds: float = Field(0.25, gt=0)
    """Time between Frames."""
    camera_offline_minutes: float = Field(10, gt=0)
    """No picture for this long makes a `camera_offline` Event."""


class LabelingSettings(_Strict):
    """The labeling page (`make label`): label clips for one Model."""

    model: str = "model_x"
    """The Model the labels are for; they are saved in `labels/<model>.csv`."""
    clips: Path = Path("clips")
    """Folder of clips saved from the Google Home app; relative: inside private_data."""
    labels: list[str] = []
    """The labels to choose from, such as ["person", "nobody"]."""


class AlexaSkillSettings(_Strict):
    """The Alexa skill endpoint the watcher serves (docs/alexa.md).

    The skill ID is not here: it comes from `CAMWATCH_ALEXA_SKILL_ID` in `.env`.
    """

    enabled: bool = False
    invocation: str = "camera watch"
    """What people say to open the skill: "Alexa, ask camera watch ..."."""
    host: str = "127.0.0.1"
    """Where the endpoint listens; the tunnel connects to it on this machine."""
    port: int = Field(8767, ge=0, le=65535)
    """0 picks any free port (for tests; a tunnel needs a fixed one)."""
    tunnel: Literal["cloudflare", "tailscale"] = "cloudflare"
    """What brings `/alexa` from the internet: Cloudflare Tunnel or Tailscale Funnel."""
    hostname: str | None = None
    """The public host name of a Cloudflare Tunnel, e.g. `watch.example.com`."""
    smart_home: bool = False
    """Also serve the Smart Home skill on /alexa/smart-home (docs/alexa.md)."""


class Config(_Strict):
    """The whole private config."""

    app: AppSettings
    parts: PartChoices = PartChoices()
    paths: Paths = Paths()
    names: dict[str, str] = {}
    """Names Message templates can use, such as `subject = "the cat"` for `{subject}`."""
    listeners: list[ListenerSettings] = []
    speakers: list[SpeakerSettings] = []
    messages: dict[str, str] = {}
    quiet_hours: list[QuietHours] = []
    states: dict[str, StateSettings] = {}
    models: dict[str, dict[str, Any]] = {}
    """Options for each Model, one `[models.<name>]` table each."""
    watcher: WatcherSettings = WatcherSettings()
    labeling: LabelingSettings = LabelingSettings()
    alexa_skill: AlexaSkillSettings = AlexaSkillSettings()
    # Options for the chosen implementation of each part.
    camera: dict[str, Any] = {}
    event_log: dict[str, Any] = {}
    state_store: dict[str, Any] = {}
    presence: dict[str, Any] = {}
    communications: dict[str, Any] = {}

    def part_options(self, kind: PartKind) -> dict[str, Any]:
        """The `[<kind>]` table: options for the chosen implementation of that part."""
        return getattr(self, kind)

    def state_settings(self, name: str) -> StateSettings:
        """`[states.<name>]`, or the defaults."""
        return self.states.get(name, StateSettings())

    @property
    def zone(self) -> ZoneInfo:
        """`app.timezone` as a ZoneInfo."""
        return ZoneInfo(self.app.timezone)


def config_path() -> Path:
    """The config file to use: `$CAMWATCH_CONFIG`, else `./config.toml`."""
    return Path(os.environ.get("CAMWATCH_CONFIG", "config.toml"))


def load_config(path: Path | None = None) -> Config:
    """Read and check the config file, raising `ConfigError` with a readable reason."""
    path = path or config_path()
    try:
        data = tomllib.loads(path.read_text())
    except FileNotFoundError:
        raise ConfigError(
            f"{path} not found; copy config.example.toml to it (`make setup`)"
        ) from None
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path}: {error}") from None
    try:
        return Config.model_validate(data)
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in e['loc'])}: {e['msg']}" for e in error.errors()
        )
        raise ConfigError(f"{path}: {problems}") from None
