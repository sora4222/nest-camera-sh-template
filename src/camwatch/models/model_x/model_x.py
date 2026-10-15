"""Model X: runs an ONNX object detector and says what it found.

The example uses a ready-trained person detector (SSD MobileNet, COCO) from the TF2
model zoo, exported to ONNX once with `make model-x` (see `model_x_export.py`). It takes
one RGB picture `[1, H, W, 3]` and gives `detection_boxes` (`[ymin, xmin, ymax, xmax]`
fractions), `detection_classes`, `detection_scores` and `num_detections`.

TODO(template): replace this with your own Model, or keep it and add Model Y beside it.
"""

import re
from collections.abc import Mapping
from typing import Any

import numpy as np

from camwatch.config import Config, ConfigError
from camwatch.domain import Frame
from camwatch.model_output import ModelOutput
from camwatch.models.model_x.model_x_schema import Found, ModelXOutput
from camwatch.onnx_session import RUNTIMES, open_session
from camwatch.registry import DEFAULT, MODEL

NAME = "model_x"
COCO_LABELS = {1: "person"}
"""Class ids of the TF model zoo COCO label map that are kept, by default."""

_PORT_SUFFIX = re.compile(r":\d+$")


class ModelX:
    """Runs an ONNX Runtime session and keeps the labelled classes above `min_score`."""

    def __init__(self, session: Any, labels: Mapping[int, str], min_score: float = 0.5) -> None:
        """`session` is an `onnxruntime.InferenceSession` (or a fake with the same methods)."""
        self._session = session
        self._labels = dict(labels)
        self._min_score = min_score
        self._input = session.get_inputs()[0]
        self._outputs = [_PORT_SUFFIX.sub("", port.name) for port in session.get_outputs()]

    def run(self, frame: Frame, output: ModelOutput) -> ModelXOutput:
        """What was found in `frame`. Model X does not read earlier Models' output."""
        results = self._session.run(None, {self._input.name: self._prepare(frame.image)})
        out = dict(zip(self._outputs, results, strict=True))
        count = int(out["num_detections"][0])
        found = []
        for cls, score, (top, left, bottom, right) in zip(
            out["detection_classes"][0][:count].astype(int).tolist(),
            out["detection_scores"][0][:count].tolist(),
            out["detection_boxes"][0][:count].tolist(),
            strict=True,
        ):
            if cls in self._labels and score >= self._min_score:
                found.append(
                    Found(label=self._labels[cls], score=score, box=(left, top, right, bottom))
                )
        return ModelXOutput(found=found)

    def _prepare(self, image: Any) -> np.ndarray:
        """`image` as the model's input: resized if its size is fixed, with one batch row."""
        pixels = np.asarray(image)
        _, height, width, _ = self._input.shape
        if isinstance(height, int) and isinstance(width, int):
            rows = np.arange(height) * pixels.shape[0] // height
            cols = np.arange(width) * pixels.shape[1] // width
            pixels = pixels[rows][:, cols]
        dtype = np.uint8 if self._input.type == "tensor(uint8)" else np.float32
        return pixels.astype(dtype)[None]


@DEFAULT.part(MODEL, NAME)
def _create(config: Config, options: Mapping[str, Any]) -> ModelX:
    """Model X from `[models.model_x]`: `file`, `runtime`, `min_score`, `labels`."""
    if "file" not in options:
        raise ConfigError(f"models.{NAME}.file: the .onnx file to use is missing")
    file = config.paths.private(options["file"])
    if not file.is_file():
        raise ConfigError(f"models.{NAME}.file: {file} not found (`make model-x` makes it)")
    runtime = options.get("runtime", "auto")
    if runtime not in RUNTIMES:
        raise ConfigError(f"models.{NAME}.runtime: use one of {', '.join(RUNTIMES)}")
    labels = {int(cls): label for cls, label in options.get("labels", COCO_LABELS).items()}
    return ModelX(open_session(file, runtime), labels, options.get("min_score", 0.5))
