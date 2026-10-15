from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from camwatch.config import Config, ConfigError
from camwatch.domain import Frame
from camwatch.model_output import ModelOutput
from camwatch.registry import MODEL, default_registry

pytest.importorskip("onnx")
pytest.importorskip("onnxruntime")
from tiny_detector import tiny_detector

FRAME = Frame(datetime(2026, 1, 1, tzinfo=UTC), np.zeros((6, 8, 3), np.uint8))


def config(folder: Path, **options) -> Config:
    return Config.model_validate(
        {
            "app": {"start_state": "no_one_at_desk"},
            "paths": {"private_data": str(folder)},
            "models": {"model_x": options},
        }
    )


def create(cfg: Config):
    return default_registry().create(MODEL, "model_x", cfg, cfg.models["model_x"])


def labels(cfg: Config) -> list[str]:
    return [item.label for item in create(cfg).run(FRAME, ModelOutput(FRAME)).found]


def test_runs_the_file_named_in_config(tmp_path):
    tiny_detector(tmp_path / "x.onnx")
    assert labels(config(tmp_path, file="x.onnx", runtime="cpu")) == ["person"]


def test_labels_and_minimum_score_come_from_config(tmp_path):
    tiny_detector(tmp_path / "x.onnx")
    cfg = config(tmp_path, file="x.onnx", min_score=0.3, labels={"1": "human", "18": "dog"})
    assert labels(cfg) == ["human", "dog"]


def test_absolute_file_path_is_used_as_is(tmp_path):
    file = tiny_detector(tmp_path / "x.onnx")
    create(config(tmp_path / "elsewhere", file=str(file)))


def test_missing_file_option_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match=r"models\.model_x\.file"):
        create(config(tmp_path))


def test_missing_file_is_a_config_error_that_says_how_to_make_it(tmp_path):
    with pytest.raises(ConfigError, match="make model-x"):
        create(config(tmp_path, file="nope.onnx"))


def test_unknown_runtime_is_a_config_error(tmp_path):
    tiny_detector(tmp_path / "x.onnx")
    with pytest.raises(ConfigError, match=r"models\.model_x\.runtime"):
        create(config(tmp_path, file="x.onnx", runtime="tpu"))
