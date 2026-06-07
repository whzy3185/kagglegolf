from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np


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


def _tensor_bytes(elem_type: int, dims: list[int]) -> int:
    import onnx

    if any(d <= 0 for d in dims):
        return 0
    try:
        dtype = onnx.helper.tensor_dtype_to_np_dtype(elem_type)
        return int(np.prod(dims)) * np.dtype(dtype).itemsize
    except Exception:
        return 0


def _value_info_bytes(value_info: Any) -> int:
    tensor_type = value_info.type.tensor_type
    if not tensor_type.HasField("shape"):
        return 0
    dims = []
    for dim in tensor_type.shape.dim:
        if not dim.HasField("dim_value"):
            return 0
        dims.append(int(dim.dim_value))
    return _tensor_bytes(tensor_type.elem_type, dims)


def profile_model(path: Path) -> dict[str, Any]:
    import onnx

    model = onnx.load(str(path))
    try:
        inferred = onnx.shape_inference.infer_shapes(model, strict_mode=False)
    except Exception:
        inferred = model
    graph = inferred.graph

    banned = []
    for node in graph.node:
        if node.op_type.upper() in {"LOOP", "SCAN", "NONZERO", "UNIQUE", "SCRIPT", "FUNCTION", "COMPRESS"}:
            banned.append(node.op_type)

    initializer_bytes = 0
    parameter_count = 0
    for init in model.graph.initializer:
        dims = [int(d) for d in init.dims]
        n = int(np.prod(dims)) if dims else 1
        parameter_count += n
        initializer_bytes += _tensor_bytes(init.data_type, dims)

    constant_param_count = 0
    constant_bytes = 0
    for node in model.graph.node:
        if node.op_type != "Constant":
            continue
        for attr in node.attribute:
            if attr.name == "value":
                dims = [int(d) for d in attr.t.dims]
                n = int(np.prod(dims)) if dims else 1
                constant_param_count += n
                constant_bytes += _tensor_bytes(attr.t.data_type, dims)
            elif attr.name == "value_ints":
                constant_param_count += len(attr.ints)
                constant_bytes += 8 * len(attr.ints)
            elif attr.name == "value_floats":
                constant_param_count += len(attr.floats)
                constant_bytes += 4 * len(attr.floats)

    parameter_count += constant_param_count
    initializer_bytes += constant_bytes

    io_names = {x.name for x in list(graph.input) + list(graph.output)}
    intermediate_tensor_count = 0
    intermediate_bytes_sum = 0
    intermediate_peak_proxy = 0
    largest = []
    for value_info in list(graph.value_info):
        if value_info.name in io_names:
            continue
        b = _value_info_bytes(value_info)
        if b:
            intermediate_tensor_count += 1
            intermediate_bytes_sum += b
            intermediate_peak_proxy = max(intermediate_peak_proxy, b)
            largest.append((value_info.name, b))
    largest.sort(key=lambda item: item[1], reverse=True)

    memory_proxy = initializer_bytes + intermediate_bytes_sum
    cost_proxy = memory_proxy + parameter_count
    return {
        "path": str(path),
        "onnx_load": True,
        "file_size": path.stat().st_size,
        "node_count": len(model.graph.node),
        "initializer_count": len(model.graph.initializer),
        "initializer_bytes": initializer_bytes,
        "parameter_count": parameter_count,
        "parameter_bytes": initializer_bytes,
        "intermediate_tensor_count": intermediate_tensor_count,
        "estimated_peak_memory": intermediate_peak_proxy,
        "memory_footprint_proxy": memory_proxy,
        "estimated_cost": cost_proxy,
        "estimated_utility": points(memory_proxy, parameter_count),
        "largest_memory_sources": ";".join(f"{name}:{size}" for name, size in largest[:5]),
        "banned_ops": ";".join(sorted(set(banned))),
    }


def safe_profile_model(path: Path) -> dict[str, Any]:
    try:
        return profile_model(path)
    except Exception as exc:
        return {
            "path": str(path),
            "onnx_load": False,
            "file_size": path.stat().st_size if path.exists() else 0,
            "node_count": 0,
            "initializer_count": 0,
            "initializer_bytes": 0,
            "parameter_count": 0,
            "parameter_bytes": 0,
            "intermediate_tensor_count": 0,
            "estimated_peak_memory": 0,
            "memory_footprint_proxy": 0,
            "estimated_cost": 0,
            "estimated_utility": 0.0,
            "largest_memory_sources": "",
            "banned_ops": f"profile_error:{type(exc).__name__}:{exc}",
        }
