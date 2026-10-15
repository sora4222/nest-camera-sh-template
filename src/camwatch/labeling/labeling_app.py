"""The labeling page's requests and answers, without any web server.

`GET /` is the page, `GET /api/next` the first unlabeled clip and the labels to choose
from, `GET /clips/<name>` the clip itself, and `POST /api/label` with `{"clip", "label"}`
saves a label. Only requests addressed to this machine (`localhost`, `127.0.0.1`) are
answered.
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import resources
from urllib.parse import unquote

from camwatch.labeling.clip_labels import ClipLabels

_CLIP = re.compile(r"^/clips/(.+)$")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]"}


@dataclass(frozen=True)
class Response:
    """What to send back."""

    status: int
    content_type: str
    body: bytes


def _json(data: object, status: int = 200) -> Response:
    return Response(status, "application/json", json.dumps(data).encode())


def _error(status: int, message: str) -> Response:
    return _json({"error": message}, status)


class LabelingApp:
    """Shows unlabeled clips one at a time and saves the label chosen for each."""

    def __init__(
        self,
        labels: ClipLabels,
        choices: list[str],
        model: str,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        """Label the clips in `labels` with one of `choices`, for the Model `model`."""
        self._labels = labels
        self._choices = list(choices)
        self._model = model
        self._now = now
        self._page = resources.files("camwatch.labeling").joinpath("labeling.html").read_bytes()

    def handle(self, method: str, path: str, body: bytes, host: str) -> Response:
        """Answer one request. `host` is the request's Host header."""
        if re.sub(r":\d+$", "", host) not in _LOCAL_HOSTS:
            return _error(403, "only requests to localhost are answered")
        path = path.split("?", 1)[0]
        if method == "GET" and path == "/":
            return Response(200, "text/html; charset=utf-8", self._page)
        if method == "GET" and path == "/api/next":
            waiting = self._labels.unlabeled()
            clip = waiting[0] if waiting else None
            data = {"clip": clip, "remaining": len(waiting), "labels": self._choices}
            return _json(data | {"model": self._model})
        if method == "GET" and (match := _CLIP.match(path)):
            file = self._labels.path(unquote(match[1]))
            if file is None:
                return _error(404, "no such unlabeled clip")
            return Response(200, "video/mp4", file.read_bytes())
        if method == "POST" and path == "/api/label":
            return self._label(body)
        return _error(404, "not found")

    def _label(self, body: bytes) -> Response:
        try:
            request = json.loads(body)
            clip, label = str(request["clip"]), str(request["label"])
        except (ValueError, KeyError, TypeError):
            return _error(400, "send {clip, label}")
        if label not in self._choices:
            return _error(400, f"label must be one of {', '.join(self._choices)}")
        if self._labels.path(clip) is None:
            return _error(409, "this clip is already labeled or gone; showing the next one")
        self._labels.label(clip, label, self._now())
        return _json({"clip": clip, "label": label})
