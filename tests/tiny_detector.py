"""A tiny ONNX model shaped like a TF detector, for Model X tests (needs onnx)."""

from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper


def tiny_detector(path: Path) -> Path:
    """An ONNX model shaped like a TF detector that always finds a person and a dog."""
    outputs = {
        "detection_boxes": np.array([[[0.1, 0.2, 0.5, 0.6], [0.0, 0.0, 1.0, 1.0]]], np.float32),
        "detection_classes": np.array([[1.0, 18.0]], np.float32),
        "detection_scores": np.array([[0.9, 0.4]], np.float32),
        "num_detections": np.array([2.0], np.float32),
    }
    nodes = [
        helper.make_node("Constant", [], [name], value=onnx.numpy_helper.from_array(value))
        for name, value in outputs.items()
    ]
    graph = helper.make_graph(
        nodes,
        "tiny_detector",
        [helper.make_tensor_value_info("input_tensor", TensorProto.UINT8, [1, "h", "w", 3])],
        [
            helper.make_tensor_value_info(name, TensorProto.FLOAT, list(value.shape))
            for name, value in outputs.items()
        ],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    onnx.save(model, path)
    return path
