"""Presence check that is switched off: every Listener is Unknown (counts as Away)."""

from collections.abc import Mapping
from typing import Any

from camwatch.config import Config
from camwatch.domain import Presence
from camwatch.registry import DEFAULT, PRESENCE


class PresenceOff:
    """Always says Unknown."""

    def check(self, listener: str) -> Presence:
        """Unknown, whoever `listener` is."""
        return Presence.UNKNOWN


@DEFAULT.part(PRESENCE, "off")
def _create(config: Config, options: Mapping[str, Any]) -> PresenceOff:
    return PresenceOff()
