"""Every State class by name. A State adds itself with `@register_state`."""

from camwatch.config import ConfigError
from camwatch.state import State

_STATES: dict[str, type[State]] = {}


def register_state[S: type[State]](cls: S) -> S:
    """Class decorator: make `cls` known by its `name`. Each name is used once."""
    if cls.name in _STATES and _STATES[cls.name] is not cls:
        raise ValueError(f"State {cls.name!r} is already registered")
    _STATES[cls.name] = cls
    return cls


def all_states() -> dict[str, type[State]]:
    """Every registered State, with the States in `camwatch.states` imported first."""
    import camwatch.states  # noqa: F401, PLC0415  (registers the States)

    return dict(_STATES)


def state_class(name: str) -> type[State]:
    """The State registered as `name`, or `ConfigError`."""
    states = all_states()
    if name not in states:
        known = ", ".join(sorted(states)) or "none"
        raise ConfigError(f"no State called {name!r}; registered: {known}")
    return states[name]
