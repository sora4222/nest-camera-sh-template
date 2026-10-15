from datetime import UTC, datetime
from pathlib import Path

import pytest
from fake_clock import FakeClock
from fake_video import write_clip

from camwatch.config import Config, ConfigError
from camwatch.parts.video_file_camera import VideoFileCamera
from camwatch.registry import CAMERA, default_registry
from camwatch.video import read_frames

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def brightness(camera: VideoFileCamera, reads: int) -> list[int | None]:
    frames = [camera.read() for _ in range(reads)]
    return [None if f is None else round(float(f.image.mean()) / 100) for f in frames]


def test_gives_the_clip_frames_in_order_then_starts_again(tmp_path):
    clip = write_clip(tmp_path / "c.mp4", [0, 100, 200])
    camera = VideoFileCamera(lambda: read_frames(clip, 0), FakeClock(NOW).now)
    assert brightness(camera, 4) == [0, 1, 2, 0]


def test_without_loop_it_stops_at_the_end(tmp_path):
    clip = write_clip(tmp_path / "c.mp4", [0, 200])
    camera = VideoFileCamera(lambda: read_frames(clip, 0), FakeClock(NOW).now, loop=False)
    assert brightness(camera, 4) == [0, 2, None, None]


def test_frames_are_stamped_with_the_time_now(tmp_path):
    clip = write_clip(tmp_path / "c.mp4", [0])
    clock = FakeClock(NOW)
    frame = VideoFileCamera(lambda: read_frames(clip, 0), clock.now).read()
    assert frame is not None and frame.taken_at == NOW


def config(folder: Path, **camera) -> Config:
    data = {"app": {"start_state": "a"}, "paths": {"private_data": str(folder)}, "camera": camera}
    return Config.model_validate(data)


def test_built_from_config_with_the_file_inside_private_data(tmp_path):
    (tmp_path / "clips").mkdir()
    write_clip(tmp_path / "clips" / "c.mp4", [0, 200])
    cfg = config(tmp_path, file="clips/c.mp4", every_seconds=0)
    camera = default_registry().create(CAMERA, "video_file", cfg, cfg.camera)
    assert camera.read() is not None


def test_a_missing_file_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match=r"camera\.file"):
        default_registry().create(CAMERA, "video_file", config(tmp_path), {})
    cfg = config(tmp_path, file="none.mp4")
    with pytest.raises(ConfigError, match="not found"):
        default_registry().create(CAMERA, "video_file", cfg, cfg.camera)
