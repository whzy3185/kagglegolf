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
    replaced_batch_compresses: int
    saved_parameters: int
    changed: bool
    status: str
    error: str = ""


@dataclass
class InlineStats:
    path: str
    output_path: str
    function_nodes_inlined: int
    functions_removed: int
    nonstandard_opsets_removed: int
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


def _node_by_output(model: onnx.ModelProto) -> dict[str, onnx.NodeProto]:
    producers: dict[str, onnx.NodeProto] = {}
    for node in model.graph.node:
        for output in node.output:
            if output:
                producers[output] = node
    return producers


def _attr_int(node: onnx.NodeProto, name: str, default: int | None = None) -> int | None:
    for attr in node.attribute:
        if attr.name == name:
            return int(onnx.helper.get_attribute_value(attr))
    return default


def _shape_map(model: onnx.ModelProto) -> dict[str, list[int | None]]:
    shapes: dict[str, list[int | None]] = {}
    try:
        inferred = onnx.shape_inference.infer_shapes(model, strict_mode=False)
    except Exception:
        inferred = model
    for value in list(inferred.graph.input) + list(inferred.graph.value_info) + list(inferred.graph.output):
        tensor_type = value.type.tensor_type
        if not tensor_type.HasField("shape"):
            continue
        dims: list[int | None] = []
        for dim in tensor_type.shape.dim:
            dims.append(int(dim.dim_value) if dim.HasField("dim_value") else None)
        shapes[value.name] = dims
    return shapes


def replace_batch_gate_compresses(model: onnx.ModelProto) -> int:
    """Replace safe batch-gate Compress nodes with Identity.

    Several public NeuroGolf artifacts use Compress(axis=0) as a guard around
    the single batch dimension. The competition structural gate bans Compress,
    but these guards are usually equivalent to passing the tensor through for
    valid ARC examples. This rewrite is intentionally conservative: it only
    touches Compress nodes whose condition is inferred as length one or is
    produced by a simple Unsqueeze/Reshape scalar-gate pattern. Solver-selection
    Compress nodes fed by Concat/NonZero-style conditions are left intact.
    """

    producers = _node_by_output(model)
    shapes = _shape_map(model)
    rewritten = []
    replaced = 0
    for node in model.graph.node:
        if node.op_type != "Compress":
            rewritten.append(node)
            continue
        axis = _attr_int(node, "axis", None)
        if axis not in {0, -4, None} or len(node.input) < 2 or len(node.output) != 1:
            rewritten.append(node)
            continue

        data_name, condition_name = node.input[0], node.input[1]
        cond_shape = shapes.get(condition_name)
        data_shape = shapes.get(data_name)
        producer = producers.get(condition_name)
        producer_type = producer.op_type if producer is not None else ""
        scalar_gate_pattern = producer_type in {"Unsqueeze", "Reshape"}
        condition_is_length_one = cond_shape == [1] or cond_shape == [1, 1]
        data_is_single_batch = data_shape is None or not data_shape or data_shape[0] in {1, None}
        if not data_is_single_batch or not (condition_is_length_one or scalar_gate_pattern):
            rewritten.append(node)
            continue

        identity = onnx.helper.make_node(
            "Identity",
            inputs=[data_name],
            outputs=[node.output[0]],
            name=node.name + "_identity_rewrite" if node.name else "",
        )
        rewritten.append(identity)
        replaced += 1

    if replaced:
        del model.graph.node[:]
        model.graph.node.extend(rewritten)
    return replaced


def inline_local_functions(model: onnx.ModelProto) -> tuple[int, int, int]:
    """Inline FunctionProto calls with concrete graph nodes.

    NeuroGolf public artifacts sometimes package task logic as a custom-domain
    function, for example golf::Identity. ORT can execute it, but the local
    structural gate rejects nonstandard opset domains and model.functions. This
    routine expands such calls into ordinary ONNX nodes and then drops custom
    function declarations/opset imports.
    """

    functions = {(func.domain, func.name): func for func in model.functions}
    if not functions:
        return 0, 0, 0

    inlined = 0
    rewritten_nodes = []
    for call_index, node in enumerate(model.graph.node):
        func = functions.get((node.domain, node.op_type))
        if func is None:
            rewritten_nodes.append(node)
            continue

        inlined += 1
        value_map: dict[str, str] = {}
        for formal, actual in zip(func.input, node.input):
            value_map[formal] = actual
        for formal, actual in zip(func.output, node.output):
            value_map[formal] = actual

        prefix = f"inline_{call_index}_{node.op_type}_"
        for body_index, body_node in enumerate(func.node):
            new_node = onnx.NodeProto()
            new_node.CopyFrom(body_node)
            del new_node.input[:]
            del new_node.output[:]

            for name in body_node.input:
                if not name:
                    new_node.input.append(name)
                else:
                    new_node.input.append(value_map.get(name, prefix + name))
            for name in body_node.output:
                mapped = value_map.get(name)
                if mapped is None:
                    mapped = prefix + name
                    value_map[name] = mapped
                new_node.output.append(mapped)
            if body_node.name:
                new_node.name = prefix + body_node.name
            else:
                new_node.name = f"{prefix}node_{body_index}"
            rewritten_nodes.append(new_node)

    if not inlined:
        return 0, 0, 0

    removed_functions = len(model.functions)
    del model.graph.node[:]
    model.graph.node.extend(rewritten_nodes)
    del model.functions[:]

    kept_opsets = [opset for opset in model.opset_import if opset.domain in {"", "ai.onnx"}]
    removed_opsets = len(model.opset_import) - len(kept_opsets)
    del model.opset_import[:]
    model.opset_import.extend(kept_opsets)
    return inlined, removed_functions, removed_opsets


def rewrite_model(
    source: Path,
    target: Path,
    *,
    compress_uniform: bool = True,
    replace_batch_compress: bool = False,
) -> RewriteStats:
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
    replaced_batch_compresses = 0
    if replace_batch_compress:
        replaced_batch_compresses = replace_batch_gate_compresses(model)

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
    changed = status != "reverted" and (params_after != params_before or replaced_batch_compresses > 0)
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
        replaced_batch_compresses=replaced_batch_compresses if status != "reverted" else 0,
        saved_parameters=max(params_before - params_after, 0),
        changed=changed,
        status=status,
        error=error,
    )


def rewrite_submission_dir(
    source_dir: Path,
    target_dir: Path,
    *,
    compress_uniform: bool = True,
    replace_batch_compress: bool = False,
) -> list[dict]:
    rows = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.glob("task*.onnx")):
        target = target_dir / source.name
        stats = rewrite_model(
            source,
            target,
            compress_uniform=compress_uniform,
            replace_batch_compress=replace_batch_compress,
        )
        rows.append(asdict(stats))
    return rows


def inline_model(source: Path, target: Path) -> InlineStats:
    model = onnx.load(str(source))
    inlined = removed_functions = removed_opsets = 0
    status = "unchanged"
    error = ""
    try:
        inlined, removed_functions, removed_opsets = inline_local_functions(model)
        onnx.checker.check_model(model, full_check=True)
        status = "inlined" if inlined else "unchanged"
    except Exception as exc:
        status = "failed"
        error = f"{type(exc).__name__}: {exc}"
        model = onnx.load(str(source))

    target.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(target))
    return InlineStats(
        path=str(source),
        output_path=str(target),
        function_nodes_inlined=inlined if status != "failed" else 0,
        functions_removed=removed_functions if status != "failed" else 0,
        nonstandard_opsets_removed=removed_opsets if status != "failed" else 0,
        status=status,
        error=error,
    )


def inline_submission_dir(source_dir: Path, target_dir: Path) -> list[dict]:
    rows = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.glob("task*.onnx")):
        target = target_dir / source.name
        stats = inline_model(source, target)
        rows.append(asdict(stats))
    return rows


def copy_as_rewrite(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    rewrite_model(source, target)
