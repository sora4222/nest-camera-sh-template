"""States people ask for (through Alexa), waiting for the watcher to move to them.

The Alexa skill answers on its own threads; the watcher takes the requests on its next
check, so only the watcher ever changes the State.
"""

import threading


class StateRequests:
    """A thread-safe list of State names asked for."""

    def __init__(self) -> None:
        """Nothing asked for yet."""
        self._lock = threading.Lock()
        self._names: list[str] = []

    def ask(self, name: str) -> None:
        """Ask the watcher to move to the State registered as `name`."""
        with self._lock:
            self._names.append(name)

    def take(self) -> list[str]:
        """Every name asked for since the last call, oldest first."""
        with self._lock:
            names, self._names = self._names, []
        return names
