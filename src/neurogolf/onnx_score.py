from __future__ import annotations

import math
from pathlib import Path


def count_initializer_params(path: Path) -> int:
    import onnx

    model = onnx.load(str(path))
    total = 0
    for init in model.graph.initializer:
        n = 1
        for d in init.dims:
            n *= d
        total += n
    for node in model.graph.node:
        if node.op_type == "Constant":
            for attr in node.attribute:
                if attr.name == "value":
                    n = 1
                    for d in attr.t.dims:
                        n *= d
                    total += n
    return total


def points(memory_bytes: int, params: int) -> float:
    return max(1.0, 25.0 - math.log(max(1.0, memory_bytes + params)))

