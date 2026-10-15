"""The example app from config to Events, with nothing faked but the clock.

It uses the video file camera, Model X (a tiny ONNX model that always finds a person),
the example States and the log speaker.

TODO(template): keep a test like this for your own app.
"""

from datetime import UTC, datetime

import pytest
from fake_clock import FakeClock
from fake_video import write_clip

from camwatch.config import Config
from camwatch.parts.memory_event_log import MemoryEventLog
from camwatch.registry import EVENT_LOG, default_registry
from camwatch.watcher.command import start_watcher

pytest.importorskip("onnx")
pytest.importorskip("onnxruntime")
from tiny_detector import tiny_detector

START = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)


def test_a_person_in_the_clip_moves_the_app_to_person_at_desk(tmp_path, caplog):
    (tmp_path / "clips").mkdir()
    (tmp_path / "models").mkdir()
    write_clip(tmp_path / "clips" / "example.mp4", [100] * 4)
    tiny_detector(tmp_path / "models" / "model_x.onnx")
    log = MemoryEventLog()
    registry = default_registry().copy()
    config = Config.model_validate(
        {
            "app": {"start_state": "no_one_at_desk"},
            "parts": {"event_log": "kept"},
            "paths": {"private_data": str(tmp_path), "lock_file": str(tmp_path / "lock")},
            "camera": {"file": "clips/example.mp4", "every_seconds": 0},
            "models": {"model_x": {"file": "models/model_x.onnx", "runtime": "cpu"}},
            "messages": {"person_at_desk_entered": "Hello {subject}."},
            "names": {"subject": "Sam"},
            "speakers": [{"name": "Log", "kind": "log"}],
        }
    )
    registry.add(EVENT_LOG, "kept", lambda config, options: log)
    checks = iter(range(8))
    with caplog.at_level("INFO"):
        assert (
            start_watcher(config, registry, FakeClock(START), lambda: next(checks, None) is None)
            == 0
        )
    kinds = [event.kind for event in log.recent(10)][::-1]
    assert kinds == ["no_one_at_desk_left", "person_at_desk_entered"]
    assert log.recent(1)[0].model_output["model_x"]["found"][0]["label"] == "person"
    assert "Log: Hello Sam." in caplog.text
