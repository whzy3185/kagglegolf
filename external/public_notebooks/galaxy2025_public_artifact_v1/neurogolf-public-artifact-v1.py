from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path


NUM_TASKS = 400
TASK_NAMES = [f"task{task_id:03d}.onnx" for task_id in range(1, NUM_TASKS + 1)]
INPUT_ROOT = Path("/kaggle/input")
WORKING = Path("/kaggle/working")
COMPETITION_DIR = INPUT_ROOT / "competitions" / "neurogolf-2026"
OUTPUT_ZIP = WORKING / "submission.zip"
AUDIT_CSV = WORKING / "identity_surgical_6272_v1_audit.csv"

SAFE_BROADCAST_OPS = {
    "Greater",
    "Less",
    "Equal",
    "Add",
    "Sub",
    "Mul",
    "Div",
    "Where",
    "Max",
    "Min",
    "And",
    "Or",
    "Not",
    "Clip",
    "LessOrEqual",
    "GreaterOrEqual",
    "Sum",
}

# Public notebook evidence flags task158 as locally passable but grader-fragile
# after scalar compression. It still receives prune and dedup transforms.
SKIP_SCALAR_COMPRESSION = {158}


def ensure_dependencies() -> None:
    missing = []
    for package, import_name in [("onnx", "onnx"), ("onnxruntime", "onnxruntime"), ("onnx-tool", "onnx_tool")]:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package)
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])


def load_utils():
    for path in [
        COMPETITION_DIR / "neurogolf_utils" / "neurogolf_utils.py",
        COMPETITION_DIR / "neurogolf_utils.py",
    ]:
        if path.exists():
            spec = importlib.util.spec_from_file_location("official_neurogolf_utils", path)
            module = importlib.util.module_from_spec(spec)
            assert spec is not None and spec.loader is not None
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("official neurogolf_utils.py not found")


def valid_task_name(name: str) -> bool:
    return name in TASK_NAMES


def read_task_zip(zip_path: Path, extract_root: Path) -> dict[str, Path]:
    target = extract_root / zip_path.stem
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(target)
    return read_task_dir(target)


def read_task_dir(directory: Path) -> dict[str, Path]:
    tasks = {}
    for path in directory.rglob("task*.onnx"):
        if valid_task_name(path.name):
            tasks[path.name] = path
    return tasks


def read_tasks(path: Path, extract_root: Path) -> dict[str, Path]:
    if path.is_file():
        return read_task_zip(path, extract_root)
    return read_task_dir(path)


def candidate_roots() -> list[Path]:
    roots = []
    for root in [INPUT_ROOT / "neurogolf-6272-50-minimal-onnx-assets-v1", INPUT_ROOT]:
        if root.exists():
            roots.append(root)
            roots.extend(path for path in root.rglob("*") if path.is_dir())
    return roots


def find_asset_paths() -> tuple[Path, Path]:
    for root in candidate_roots():
        base_zip = root / "base_submission.zip"
        overrides_zip = root / "overrides.zip"
        if base_zip.exists() and overrides_zip.exists():
            return base_zip, overrides_zip

        base_dir = root / "base_submission"
        overrides_dir = root / "overrides"
        if base_dir.is_dir() and overrides_dir.is_dir():
            return base_dir, overrides_dir
    raise FileNotFoundError("Kojimar 6272 base_submission and overrides assets not found")


def load_examples(task_id: int) -> dict:
    path = COMPETITION_DIR / f"task{task_id:03d}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def audit_one(utils, onnx_path: Path, examples: dict) -> dict:
    import onnx
    import onnxruntime

    excluded = {"LOOP", "SCAN", "NONZERO", "UNIQUE", "SCRIPT", "FUNCTION", "COMPRESS"}
    result = {
        "status": "ok",
        "cost": None,
        "points": 0.0,
        "n_pass": 0,
        "n_fail": 0,
        "error": "",
    }
    if onnx_path.stat().st_size > 1.44 * 1024 * 1024:
        result["status"] = "FILESIZE_OVER_LIMIT"
        return result
    try:
        model = onnx.load(str(onnx_path))
        for node in model.graph.node:
            if node.op_type.upper() in excluded or "Sequence" in node.op_type:
                result["status"] = f"BANNED_OP:{node.op_type}"
                return result
        sanitized = utils.sanitize_model(onnx.load(str(onnx_path)))
        if not sanitized:
            result["status"] = "sanitize_failed"
            return result
        opts = onnxruntime.SessionOptions()
        opts.enable_profiling = True
        opts.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_DISABLE_ALL
        opts.profile_file_prefix = str(Path(tempfile.gettempdir()) / f"audit_{onnx_path.stem}")
        session = onnxruntime.InferenceSession(sanitized.SerializeToString(), opts)
        for key in ["train", "test", "arc-gen"]:
            block = examples.get(key, [])
            if isinstance(block, dict):
                block = block.get("challenges", [])
            for example in block:
                benchmark = utils.convert_to_numpy(example)
                if benchmark is None:
                    continue
                try:
                    pred = session.run(["output"], {"input": benchmark["input"]})[0]
                    pred = (pred > 0.0).astype("float32")
                    if (pred == benchmark["output"]).all():
                        result["n_pass"] += 1
                    else:
                        result["n_fail"] += 1
                except Exception as exc:
                    result["n_fail"] += 1
                    if not result["error"]:
                        result["error"] = f"{type(exc).__name__}: {exc}"
        trace_path = session.end_profiling()
        try:
            memory = utils.calculate_memory(sanitized, trace_path)
            params = utils.calculate_params(sanitized)
        finally:
            try:
                os.remove(trace_path)
            except OSError:
                pass
        if memory is None or params is None:
            result["status"] = "unscorable"
            return result
        cost = int(memory + params)
        result["cost"] = cost
        if result["n_fail"]:
            result["status"] = "INCORRECT"
            return result
        result["points"] = max(1.0, 25.0 - math.log(max(1, cost)))
        return result
    except Exception as exc:
        result["status"] = f"error:{type(exc).__name__}"
        result["error"] = str(exc)
        return result


def initializer_param_count(init) -> int:
    import numpy as np

    if not init.dims:
        return 1
    return int(np.prod(init.dims))


def cleanup_unused_initializers(model) -> tuple[int, int]:
    used = set()
    for node in model.graph.node:
        used.update(name for name in node.input if name)
    used.update(out.name for out in model.graph.output)

    removed_count = 0
    saved_params = 0
    for init in list(model.graph.initializer):
        if init.name not in used:
            saved_params += initializer_param_count(init)
            model.graph.initializer.remove(init)
            removed_count += 1
    return removed_count, saved_params


def initializer_key(init):
    from onnx import numpy_helper

    arr = numpy_helper.to_array(init)
    return arr.dtype.str, tuple(arr.shape), arr.tobytes()


def deduplicate_initializers(model) -> tuple[int, int]:
    groups = defaultdict(list)
    init_by_name = {init.name: init for init in model.graph.initializer}
    for init in model.graph.initializer:
        groups[initializer_key(init)].append(init.name)

    replace = {}
    saved_params = 0
    for names in groups.values():
        if len(names) <= 1:
            continue
        canonical = sorted(names, key=lambda value: (len(value), value))[0]
        for name in names:
            if name != canonical:
                replace[name] = canonical
                saved_params += initializer_param_count(init_by_name[name])

    if not replace:
        return 0, 0

    for node in model.graph.node:
        for idx, name in enumerate(node.input):
            if name in replace:
                node.input[idx] = replace[name]

    graph_outputs = {out.name for out in model.graph.output}
    used = {name for node in model.graph.node for name in node.input if name}
    used.update(graph_outputs)
    kept = [init for init in model.graph.initializer if init.name in used]
    del model.graph.initializer[:]
    model.graph.initializer.extend(kept)
    return len(replace), saved_params


def compress_uniform_initializers(model) -> tuple[int, int]:
    import numpy as np
    from onnx import numpy_helper

    arrays = {init.name: numpy_helper.to_array(init) for init in model.graph.initializer}
    consumers: dict[str, list[str]] = defaultdict(list)
    for node in model.graph.node:
        for name in node.input:
            if name in arrays:
                consumers[name].append(node.op_type)

    graph_outputs = {out.name for out in model.graph.output}
    compressed_count = 0
    saved_params = 0
    for init in model.graph.initializer:
        if init.name in graph_outputs:
            continue
        arr = arrays[init.name]
        size = max(int(np.prod(arr.shape)), 1)
        if size <= 1:
            continue
        flat = arr.ravel()
        if not np.all(flat == flat[0]):
            continue
        consumer_ops = set(consumers.get(init.name, []))
        if not consumer_ops or not consumer_ops <= SAFE_BROADCAST_OPS:
            continue

        scalar = np.array(flat[0], dtype=arr.dtype)
        init.CopyFrom(numpy_helper.from_array(scalar, init.name))
        compressed_count += 1
        saved_params += size - 1
    return compressed_count, saved_params


def compress_broadcast_axes(array):
    import numpy as np

    if array.ndim == 0 or array.size <= 1:
        return None

    compressed = array
    changed = False
    for axis, dim in enumerate(array.shape):
        if dim <= 1:
            continue
        first_slice = np.take(compressed, [0], axis=axis)
        if np.all(compressed == first_slice):
            compressed = first_slice
            changed = True

    if not changed or compressed.size >= array.size:
        return None
    return compressed


def compress_axis_broadcast_initializers(model) -> tuple[int, int]:
    from onnx import numpy_helper

    consumers: dict[str, list[str]] = defaultdict(list)
    for node in model.graph.node:
        for name in node.input:
            consumers[name].append(node.op_type)

    graph_outputs = {out.name for out in model.graph.output}
    compressed_count = 0
    saved_params = 0
    for init in model.graph.initializer:
        if init.name in graph_outputs:
            continue
        consumer_ops = set(consumers.get(init.name, []))
        if not consumer_ops or not consumer_ops <= SAFE_BROADCAST_OPS:
            continue

        array = numpy_helper.to_array(init)
        compressed = compress_broadcast_axes(array)
        if compressed is None:
            continue

        init.CopyFrom(numpy_helper.from_array(compressed.astype(array.dtype, copy=False), init.name))
        compressed_count += 1
        saved_params += int(array.size - compressed.size)

    return compressed_count, saved_params


def constant_tensor_attribute(node):
    if node.op_type != "Constant" or len(node.output) != 1:
        return None
    for attr in node.attribute:
        if attr.name == "value" and attr.HasField("t"):
            return attr
    return None


def compress_axis_broadcast_constants(model) -> tuple[int, int]:
    from onnx import numpy_helper

    consumers: dict[str, list[str]] = defaultdict(list)
    for node in model.graph.node:
        for name in node.input:
            consumers[name].append(node.op_type)

    graph_outputs = {out.name for out in model.graph.output}
    compressed_count = 0
    saved_params = 0
    for node in model.graph.node:
        attr = constant_tensor_attribute(node)
        if attr is None or node.output[0] in graph_outputs:
            continue
        consumer_ops = set(consumers.get(node.output[0], []))
        if not consumer_ops or not consumer_ops <= SAFE_BROADCAST_OPS:
            continue

        array = numpy_helper.to_array(attr.t)
        compressed = compress_broadcast_axes(array)
        if compressed is None:
            continue

        attr.t.CopyFrom(numpy_helper.from_array(compressed.astype(array.dtype, copy=False), attr.t.name))
        compressed_count += 1
        saved_params += int(array.size - compressed.size)

    return compressed_count, saved_params


def eliminate_identity_nodes(model) -> tuple[int, int]:
    graph_outputs = {out.name for out in model.graph.output}
    replacements = {}
    for node in model.graph.node:
        if node.op_type != "Identity" or len(node.input) != 1 or len(node.output) != 1:
            continue
        if node.output[0] in graph_outputs:
            continue
        replacements[node.output[0]] = node.input[0]

    if not replacements:
        return 0, 0

    def resolve(name: str) -> str:
        seen = set()
        while name in replacements and name not in seen:
            seen.add(name)
            name = replacements[name]
        return name

    rewired = 0
    kept_nodes = []
    for node in model.graph.node:
        for idx, name in enumerate(node.input):
            if name in replacements:
                node.input[idx] = resolve(name)
                rewired += 1
        if node.op_type == "Identity" and node.output and node.output[0] in replacements:
            continue
        kept_nodes.append(node)

    removed = len(model.graph.node) - len(kept_nodes)
    del model.graph.node[:]
    model.graph.node.extend(kept_nodes)
    return removed, rewired


def optimize_task(task_id: int, path: Path) -> dict:
    import onnx

    original = path.read_bytes()
    model = onnx.load(str(path))
    prune_count, prune_saved = cleanup_unused_initializers(model)
    dedup_count, dedup_saved = deduplicate_initializers(model)
    scalar_count = 0
    scalar_saved = 0
    if task_id not in SKIP_SCALAR_COMPRESSION:
        scalar_count, scalar_saved = compress_uniform_initializers(model)
    axis_count, axis_saved = compress_axis_broadcast_initializers(model)
    const_axis_count, const_axis_saved = compress_axis_broadcast_constants(model)
    identity_count, identity_rewired = eliminate_identity_nodes(model)

    if prune_count or dedup_count or scalar_count or axis_count or const_axis_count or identity_count:
        try:
            onnx.checker.check_model(model)
            del model.graph.value_info[:]
            onnx.shape_inference.infer_shapes(model, strict_mode=True)
            onnx.save(model, str(path))
        except Exception:
            path.write_bytes(original)
            return {
                "changed": False,
                "reverted": True,
                "prune_count": prune_count,
                "prune_saved": prune_saved,
                "dedup_count": dedup_count,
                "dedup_saved": dedup_saved,
                "scalar_count": scalar_count,
                "scalar_saved": scalar_saved,
                "axis_count": axis_count,
                "axis_saved": axis_saved,
                "const_axis_count": const_axis_count,
                "const_axis_saved": const_axis_saved,
                "identity_count": identity_count,
                "identity_rewired": identity_rewired,
            }

    return {
        "changed": bool(prune_count or dedup_count or scalar_count or axis_count or const_axis_count or identity_count),
        "reverted": False,
        "prune_count": prune_count,
        "prune_saved": prune_saved,
        "dedup_count": dedup_count,
        "dedup_saved": dedup_saved,
        "scalar_count": scalar_count,
        "scalar_saved": scalar_saved,
        "axis_count": axis_count,
        "axis_saved": axis_saved,
        "const_axis_count": const_axis_count,
        "const_axis_saved": const_axis_saved,
        "identity_count": identity_count,
        "identity_rewired": identity_rewired,
    }


def write_zip(stage: Path) -> None:
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in TASK_NAMES:
            archive.write(stage / name, arcname=name)
    with zipfile.ZipFile(OUTPUT_ZIP) as archive:
        names = sorted(info.filename for info in archive.infolist() if not info.is_dir())
        assert names == TASK_NAMES, (len(names), names[:3], names[-3:])


def main() -> None:
    ensure_dependencies()
    utils = load_utils()
    base_asset, overrides_asset = find_asset_paths()
    print("base asset:", base_asset)
    print("overrides asset:", overrides_asset)

    with tempfile.TemporaryDirectory(prefix="surgical_6272_") as tmp:
        tmp_root = Path(tmp)
        extract_root = tmp_root / "extract"
        stage = tmp_root / "stage"
        stage.mkdir(parents=True)

        base_tasks = read_tasks(base_asset, extract_root)
        override_tasks = read_tasks(overrides_asset, extract_root)
        if sorted(base_tasks) != TASK_NAMES:
            raise RuntimeError(f"Expected 400 base tasks, found {len(base_tasks)}")
        merged = dict(base_tasks)
        merged.update(override_tasks)
        if sorted(merged) != TASK_NAMES:
            raise RuntimeError(f"Expected 400 merged tasks, found {len(merged)}")

        rows = []
        status_counts: dict[str, int] = {}
        totals = {
            "changed": 0,
            "reverted": 0,
            "prune_saved": 0,
            "dedup_saved": 0,
            "scalar_saved": 0,
            "axis_saved": 0,
            "const_axis_saved": 0,
            "identity_count": 0,
        }
        for task_id, name in enumerate(TASK_NAMES, start=1):
            path = stage / name
            shutil.copy2(merged[name], path)
            before = audit_one(utils, path, load_examples(task_id))
            opt = optimize_task(task_id, path)
            after = audit_one(utils, path, load_examples(task_id))
            if after["status"] != "ok" or before["status"] != "ok" or after["points"] + 1e-12 < before["points"]:
                shutil.copy2(merged[name], path)
                opt["reverted"] = True
                opt["changed"] = False
                after = audit_one(utils, path, load_examples(task_id))

            status_counts[after["status"]] = status_counts.get(after["status"], 0) + 1
            totals["changed"] += int(opt["changed"])
            totals["reverted"] += int(opt["reverted"])
            totals["prune_saved"] += opt["prune_saved"] if opt["changed"] else 0
            totals["dedup_saved"] += opt["dedup_saved"] if opt["changed"] else 0
            totals["scalar_saved"] += opt["scalar_saved"] if opt["changed"] else 0
            totals["axis_saved"] += opt["axis_saved"] if opt["changed"] else 0
            totals["const_axis_saved"] += opt["const_axis_saved"] if opt["changed"] else 0
            totals["identity_count"] += opt["identity_count"] if opt["changed"] else 0
            rows.append({
                "task": name,
                "source": "override" if name in override_tasks else "base",
                "status": after["status"],
                "before_cost": before["cost"],
                "after_cost": after["cost"],
                "before_points": f"{before['points']:.8f}",
                "after_points": f"{after['points']:.8f}",
                "delta_points": f"{after['points'] - before['points']:.8f}",
                "changed": opt["changed"],
                "reverted": opt["reverted"],
                "prune_saved": opt["prune_saved"] if opt["changed"] else 0,
                "dedup_saved": opt["dedup_saved"] if opt["changed"] else 0,
                "scalar_saved": opt["scalar_saved"] if opt["changed"] else 0,
                "axis_saved": opt["axis_saved"] if opt["changed"] else 0,
                "const_axis_saved": opt["const_axis_saved"] if opt["changed"] else 0,
                "identity_count": opt["identity_count"] if opt["changed"] else 0,
                "identity_rewired": opt["identity_rewired"] if opt["changed"] else 0,
                "n_pass": after["n_pass"],
                "n_fail": after["n_fail"],
                "error": after["error"],
            })
            if task_id % 25 == 0:
                print(f"audited {task_id}/{NUM_TASKS}")

        with AUDIT_CSV.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        write_zip(stage)

    total_before = sum(float(row["before_points"]) for row in rows)
    total_after = sum(float(row["after_points"]) for row in rows)
    bad = [row for row in rows if row["status"] != "ok"]
    digest = hashlib.sha256(OUTPUT_ZIP.read_bytes()).hexdigest()
    print("base tasks:", len(base_tasks))
    print("override tasks:", len(override_tasks))
    print("status_counts:", status_counts)
    print("bad_count:", len(bad))
    print("optimization_totals:", totals)
    for row in bad[:20]:
        print("BAD", row)
    print(f"official-example total before: {total_before:.6f}")
    print(f"official-example total after: {total_after:.6f}")
    print(f"official-example gain: {total_after - total_before:.6f}")
    print("wrote:", OUTPUT_ZIP)
    print("zip bytes:", OUTPUT_ZIP.stat().st_size)
    print("sha256:", digest)
    print("audit_csv:", AUDIT_CSV)


if __name__ == "__main__":
    main()
