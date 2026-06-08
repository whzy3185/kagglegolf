from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import onnx
from onnx import numpy_helper


SAFE_BROADCAST_OPS = {
    "Add",
    "And",
    "Clip",
    "Div",
    "Equal",
    "Greater",
    "GreaterOrEqual",
    "Less",
    "LessOrEqual",
    "Max",
    "Min",
    "Mul",
    "Not",
    "Or",
    "Sub",
    "Sum",
    "Where",
}


@dataclass
class RewriteStats:
    path: str
    output_path: str
    node_count_before: int
    node_count_after: int
    initializer_count_before: int
    initializer_count_after: int
    parameter_count_before: int
    parameter_count_after: int
    removed_unused_initializers: int
    deduplicated_initializers: int
    scalar_compressed_initializers: int
    saved_parameters: int
    changed: bool
    status: str
    error: str = ""


def _param_count(initializers: Iterable[onnx.TensorProto]) -> int:
    total = 0
    for init in initializers:
        if init.dims:
            total += int(np.prod(init.dims))
        else:
            total += 1
    return total


def _used_initializer_names(model: onnx.ModelProto) -> set[str]:
    used: set[str] = set()
    for node in model.graph.node:
        used.update(name for name in node.input if name)
    return used


def prune_unused_initializers(model: onnx.ModelProto) -> int:
    used = _used_initializer_names(model)
    kept = [init for init in model.graph.initializer if init.name in used]
    removed = len(model.graph.initializer) - len(kept)
    if removed:
        del model.graph.initializer[:]
        model.graph.initializer.extend(kept)
    return removed


def _initializer_key(init: onnx.TensorProto) -> tuple[str, tuple[int, ...], bytes]:
    arr = numpy_helper.to_array(init)
    return (arr.dtype.str, tuple(arr.shape), arr.tobytes())


def deduplicate_initializers(model: onnx.ModelProto) -> int:
    groups: dict[tuple[str, tuple[int, ...], bytes], list[str]] = {}
    for init in model.graph.initializer:
        groups.setdefault(_initializer_key(init), []).append(init.name)

    replace: dict[str, str] = {}
    for names in groups.values():
        if len(names) <= 1:
            continue
        canonical = sorted(names, key=lambda value: (len(value), value))[0]
        for name in names:
            if name != canonical:
                replace[name] = canonical

    if not replace:
        return 0

    for node in model.graph.node:
        for idx, name in enumerate(node.input):
            if name in replace:
                node.input[idx] = replace[name]

    prune_unused_initializers(model)
    return len(replace)


def _initializer_consumers(model: onnx.ModelProto) -> dict[str, set[str]]:
    initializer_names = {init.name for init in model.graph.initializer}
    consumers: dict[str, set[str]] = {name: set() for name in initializer_names}
    for node in model.graph.node:
        for name in node.input:
            if name in consumers:
                consumers[name].add(node.op_type)
    return consumers


def compress_uniform_initializers(model: onnx.ModelProto) -> tuple[int, int]:
    consumers = _initializer_consumers(model)
    compressed = 0
    saved = 0
    for init in model.graph.initializer:
        arr = numpy_helper.to_array(init)
        size = max(int(np.prod(arr.shape)), 1)
        if size <= 1:
            continue
        flat = arr.ravel()
        if flat.size == 0 or not np.all(flat == flat[0]):
            continue
        consumer_ops = consumers.get(init.name, set())
        if not consumer_ops or not consumer_ops <= SAFE_BROADCAST_OPS:
            continue
        scalar = np.array(flat[0], dtype=arr.dtype)
        init.CopyFrom(numpy_helper.from_array(scalar, init.name))
        compressed += 1
        saved += size - 1
    return compressed, saved


def rewrite_model(source: Path, target: Path, *, compress_uniform: bool = True) -> RewriteStats:
    before = onnx.load(str(source))
    model = onnx.load(str(source))

    params_before = _param_count(model.graph.initializer)
    initializers_before = len(model.graph.initializer)
    nodes_before = len(model.graph.node)

    removed = prune_unused_initializers(model)
    deduped = deduplicate_initializers(model)
    compressed = 0
    scalar_saved = 0
    if compress_uniform:
        compressed, scalar_saved = compress_uniform_initializers(model)

    status = "unchanged"
    error = ""
    try:
        onnx.checker.check_model(model)
        onnx.shape_inference.infer_shapes(model, strict_mode=True)
    except Exception as exc:
        model = before
        status = "reverted"
        error = f"{type(exc).__name__}: {exc}"

    target.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(target))

    params_after = _param_count(model.graph.initializer)
    changed = status != "reverted" and params_after != params_before
    if changed:
        status = "rewritten"

    return RewriteStats(
        path=str(source),
        output_path=str(target),
        node_count_before=nodes_before,
        node_count_after=len(model.graph.node),
        initializer_count_before=initializers_before,
        initializer_count_after=len(model.graph.initializer),
        parameter_count_before=params_before,
        parameter_count_after=params_after,
        removed_unused_initializers=removed if status != "reverted" else 0,
        deduplicated_initializers=deduped if status != "reverted" else 0,
        scalar_compressed_initializers=compressed if status != "reverted" else 0,
        saved_parameters=max(params_before - params_after, 0),
        changed=changed,
        status=status,
        error=error,
    )


def rewrite_submission_dir(source_dir: Path, target_dir: Path, *, compress_uniform: bool = True) -> list[dict]:
    rows = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.glob("task*.onnx")):
        target = target_dir / source.name
        stats = rewrite_model(source, target, compress_uniform=compress_uniform)
        rows.append(asdict(stats))
    return rows


def copy_as_rewrite(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    rewrite_model(source, target)
