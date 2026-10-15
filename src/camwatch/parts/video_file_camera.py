"""Camera "video_file": plays a saved clip as if it were the camera.

It is for trying the app, and for tests, with no camera. One Frame per `read`, every
`every_seconds` of the clip.

TODO(template): switch `[parts] camera` to "nest" once the app works on a clip.
"""

from collections.abc import Callable, Iterator, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from camwatch.clock import SystemClock
from camwatch.config import Config, ConfigError
from camwatch.domain import Frame
from camwatch.registry import CAMERA, DEFAULT
from camwatch.video import read_frames

type Reader = Callable[[], Iterator[tuple[float, np.ndarray]]]
"""Starts reading the clip from the beginning: `(seconds, RGB array)` pairs."""


class VideoFileCamera:
    """A `CameraSource` that gives the clip's frames in order, then starts again if `loop`."""

    def __init__(self, reader: Reader, now: Callable[[], datetime], loop: bool = True) -> None:
        """Nothing is read until the first `read`."""
        self._reader = reader
        self._now = now
        self._loop = loop
        self._frames: Iterator[tuple[float, np.ndarray]] | None = None
        self._done = False

    def read(self) -> Frame | None:
        """The next frame of the clip, stamped with the time now; None once it has ended."""
        if self._done:
            return None
        if self._frames is None:
            self._frames = self._reader()
        picture = next(self._frames, None)
        if picture is None and self._loop:
            self._frames = self._reader()
            picture = next(self._frames, None)
        if picture is None:
            self._done = True
            return None
        return Frame(self._now(), picture[1])


@DEFAULT.part(CAMERA, "video_file")
def _create(config: Config, options: Mapping[str, Any]) -> VideoFileCamera:
    if "file" not in options:
        raise ConfigError("camera.file: the clip to play is missing")
    file: Path = config.paths.private(options["file"])
    if not file.is_file():
        raise ConfigError(f"camera.file: {file} not found")
    every = options.get("every_seconds", 0.5)
    return VideoFileCamera(
        lambda: read_frames(file, every), SystemClock().now, bool(options.get("loop", True))
    )
