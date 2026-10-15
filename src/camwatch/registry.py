"""Choose implementations of the swappable parts by the names given in config.

An implementation registers a factory under a name for one slot, for example
`@DEFAULT.part(PRESENCE, "wifi")`. A Model registers under its own name, for example
`@DEFAULT.part(MODEL, "model_x")`. `build_parts` makes every part the config asks for.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from camwatch.config import Config, ConfigError, PartKind
from camwatch.interfaces import (
    CameraSource,
    CommunicationsHandler,
    EventLog,
    Model,
    PresenceCheck,
    Speaker,
    StateStore,
)

type Factory[T] = Callable[[Config, Mapping[str, Any]], T]
"""Makes a part from the whole config and that part's own options."""


@dataclass(frozen=True)
class Slot[T]:
    """A kind of swappable part; `T` is the interface its implementations follow."""

    kind: str


CAMERA = Slot[CameraSource]("camera")
MODEL = Slot[Model]("model")
"""Registered by Model name (its folder name), not by kind."""
EVENT_LOG = Slot[EventLog]("event_log")
STATE_STORE = Slot[StateStore]("state_store")
PRESENCE = Slot[PresenceCheck]("presence")
COMMUNICATIONS = Slot[CommunicationsHandler]("communications")
SPEAKER = Slot[Speaker]("speaker")


class UnknownPart(ConfigError):
    """Config names an implementation that is not registered."""


class Registry:
    """Factories by slot and name."""

    def __init__(self) -> None:
        """Start empty."""
        self._factories: dict[tuple[str, str], Factory[Any]] = {}

    def add[T](self, slot: Slot[T], name: str, factory: Factory[T]) -> None:
        """Register `factory` as `name` for `slot`. Each name is used once per slot."""
        key = (slot.kind, name)
        if key in self._factories:
            raise ValueError(f"{slot.kind} {name!r} is already registered")
        self._factories[key] = factory

    def part[T](self, slot: Slot[T], name: str) -> Callable[[Factory[T]], Factory[T]]:
        """Decorator form of `add`."""

        def register(factory: Factory[T]) -> Factory[T]:
            self.add(slot, name, factory)
            return factory

        return register

    def copy(self) -> "Registry":
        """A new registry with the same factories, to add to without changing this one."""
        copied = Registry()
        copied._factories = dict(self._factories)
        return copied

    def names(self, slot: Slot[Any]) -> list[str]:
        """Registered names for `slot`, sorted."""
        return sorted(name for kind, name in self._factories if kind == slot.kind)

    def create[T](self, slot: Slot[T], name: str, config: Config, options: Mapping[str, Any]) -> T:
        """Make the part registered as `name`, or raise `UnknownPart`."""
        factory = self._factories.get((slot.kind, name))
        if factory is None:
            known = ", ".join(self.names(slot)) or "none"
            raise UnknownPart(f"no {slot.kind} called {name!r}; registered: {known}")
        return factory(config, options)


DEFAULT = Registry()
"""The registry that built-in parts in `camwatch.parts` add themselves to."""


def default_registry() -> Registry:
    """`DEFAULT`, with every built-in part and every Model registered."""
    # Local: the parts import this module to register themselves.
    import camwatch.models  # noqa: PLC0415  (registers the Models)
    import camwatch.parts  # noqa: F401, PLC0415  (registers the built-ins)

    return DEFAULT


@dataclass(frozen=True)
class Parts:
    """One of each part, as chosen in config."""

    camera: CameraSource
    event_log: EventLog
    state_store: StateStore
    communications: CommunicationsHandler


def build_parts(config: Config, registry: Registry) -> Parts:
    """Make every part named in `config.parts`."""

    def make[T](slot: Slot[T], kind: PartKind) -> T:
        name = getattr(config.parts, kind)
        return registry.create(slot, name, config, config.part_options(kind))

    return Parts(
        camera=make(CAMERA, "camera"),
        event_log=make(EVENT_LOG, "event_log"),
        state_store=make(STATE_STORE, "state_store"),
        communications=make(COMMUNICATIONS, "communications"),
    )


def build_models(config: Config, registry: Registry, names: list[str]) -> dict[str, Model]:
    """Make each Model in `names`, with its `[models.<name>]` options."""
    return {
        name: registry.create(MODEL, name, config, config.models.get(name, {})) for name in names
    }
