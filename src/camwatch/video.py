"""Read frames from an MP4 clip (PyAV)."""

from collections.abc import Iterator
from pathlib import Path

import av
import numpy as np

_EPSILON = 1e-6


class VideoError(Exception):
    """The clip cannot be read."""


def read_frames(
    path: Path, every_seconds: float, start: float = 0.0, end: float | None = None
) -> Iterator[tuple[float, np.ndarray]]:
    """`(seconds, RGB array)` for one frame every `every_seconds` from `start` to `end`.

    `every_seconds` 0 gives every frame.
    """
    try:
        with av.open(str(path)) as container:
            stream = container.streams.video[0]
            origin = 0.0
            if stream.start_time is not None and stream.time_base is not None:
                origin = float(stream.start_time * stream.time_base)
            if start > 0 and stream.time_base is not None:
                container.seek(int((start + origin) / stream.time_base), stream=stream)
            wanted = start
            for frame in container.decode(stream):
                if frame.time is None:
                    continue
                seconds = float(frame.time) - origin
                if end is not None and seconds > end + _EPSILON:
                    return
                if seconds + _EPSILON < wanted:
                    continue
                yield seconds, frame.to_ndarray(format="rgb24")
                if every_seconds <= 0:
                    continue
                while wanted <= seconds + _EPSILON:
                    wanted += every_seconds
    except (av.FFmpegError, IndexError) as error:
        raise VideoError(f"{path}: {error}") from None
