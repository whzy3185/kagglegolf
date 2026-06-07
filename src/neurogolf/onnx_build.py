from __future__ import annotations

from pathlib import Path

import numpy as np

from . import spec


def build_zero_network(path: Path) -> None:
    import onnx
    from onnx import TensorProto, helper

    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, list(spec.TENSOR_SHAPE))
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, list(spec.TENSOR_SHAPE))
    values = np.zeros(spec.TENSOR_SHAPE, dtype=np.float32).ravel()
    const = helper.make_tensor("zero", TensorProto.FLOAT, list(spec.TENSOR_SHAPE), values)
    node = helper.make_node("Constant", [], [spec.OUTPUT_NAME], value=const)
    graph = helper.make_graph([node], "zero_graph", [x], [y])
    model = helper.make_model(graph, ir_version=spec.IR_VERSION, opset_imports=[helper.make_opsetid("", spec.OPSET)])
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))

