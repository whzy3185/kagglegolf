from __future__ import annotations

import json
import re
import traceback
from dataclasses import dataclass, asdict
from pathlib import Path

from . import spec
from .data_io import exact_onehot_equal, iter_pairs, load_task, pair_to_numpy


TASK_RE = re.compile(r"^task(\d{3})\.onnx$")


@dataclass
class FileValidation:
    path: str
    ok: bool
    task_id: str | None
    size_bytes: int
    structural_errors: list[str]
    examples_checked: int = 0
    examples_passed: int = 0
    examples_failed: int = 0


def _import_onnx():
    import onnx
    import onnxruntime as ort

    return onnx, ort


def validate_onnx_file(
    path: Path,
    data_dir: Path | None = None,
    smoke_examples_per_split: int = 0,
) -> FileValidation:
    errors: list[str] = []
    m = TASK_RE.match(path.name)
    task_id = path.stem if m else None
    size = path.stat().st_size if path.exists() else 0
    if not m:
        errors.append("filename_not_taskNNN.onnx")
    if size <= 0:
        errors.append("empty_file")
    if size > spec.FILE_SIZE_LIMIT_BYTES:
        errors.append(f"file_too_large:{size}")

    examples_checked = examples_passed = examples_failed = 0
    try:
        onnx, ort = _import_onnx()
        model = onnx.load(str(path))
        onnx.checker.check_model(model, full_check=True)
        if len(model.graph.input) != 1:
            errors.append("not_single_input")
        if len(model.graph.output) != 1:
            errors.append("not_single_output")
        for opset in model.opset_import:
            if opset.domain not in {"", "ai.onnx"}:
                errors.append(f"bad_opset_domain:{opset.domain}")
        if model.functions:
            errors.append("has_functions")
        for node in model.graph.node:
            if node.op_type.upper() in spec.BANNED_OPS or "SEQUENCE" in node.op_type.upper():
                errors.append(f"banned_op:{node.op_type}")
        options = ort.SessionOptions()
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        session = ort.InferenceSession(model.SerializeToString(), options, providers=["CPUExecutionProvider"])
        if session.get_inputs()[0].name != spec.INPUT_NAME:
            errors.append(f"input_name:{session.get_inputs()[0].name}")
        if session.get_outputs()[0].name != spec.OUTPUT_NAME:
            errors.append(f"output_name:{session.get_outputs()[0].name}")
        if smoke_examples_per_split and task_id and data_dir:
            task = load_task(f"{task_id}.json", data_dir)
            split_counts = {"train": 0, "test": 0, "arc-gen": 0}
            for split, pair in iter_pairs(task):
                if split_counts[split] >= smoke_examples_per_split:
                    continue
                arrays = pair_to_numpy(pair)
                if arrays is None:
                    continue
                split_counts[split] += 1
                examples_checked += 1
                x, expected = arrays
                try:
                    output = session.run([spec.OUTPUT_NAME], {spec.INPUT_NAME: x})[0]
                    if exact_onehot_equal(output, expected):
                        examples_passed += 1
                    else:
                        examples_failed += 1
                except Exception:
                    examples_failed += 1
                    errors.append("runtime_example_error")
                    break
    except Exception as exc:
        errors.append(f"load_or_check_error:{type(exc).__name__}:{exc}")
        tb = traceback.format_exc(limit=2).replace("\n", " | ")
        errors.append(tb[:500])

    if examples_failed:
        errors.append(f"example_failures:{examples_failed}")
    return FileValidation(
        path=str(path),
        ok=not errors,
        task_id=task_id,
        size_bytes=size,
        structural_errors=errors,
        examples_checked=examples_checked,
        examples_passed=examples_passed,
        examples_failed=examples_failed,
    )


def validate_submission_dir(
    submission_dir: Path,
    data_dir: Path | None = None,
    smoke_examples_per_split: int = 0,
    max_tasks: int | None = None,
) -> dict:
    files = sorted(submission_dir.glob("task*.onnx"))
    if max_tasks:
        files = files[:max_tasks]
    results = [validate_onnx_file(p, data_dir, smoke_examples_per_split) for p in files]
    task_ids = {r.task_id for r in results if r.task_id}
    missing = [f"task{i:03d}" for i in range(1, spec.TASK_COUNT + 1) if f"task{i:03d}" not in task_ids]
    duplicate_count = len(task_ids) != len([r.task_id for r in results if r.task_id])
    payload = {
        "submission_dir": str(submission_dir),
        "file_count": len(results),
        "expected_task_count": spec.TASK_COUNT,
        "all_structural_ok": all(r.ok for r in results),
        "missing_task_count": len(missing),
        "missing_task_ids_head": missing[:20],
        "has_duplicates": duplicate_count,
        "examples_checked": sum(r.examples_checked for r in results),
        "examples_passed": sum(r.examples_passed for r in results),
        "examples_failed": sum(r.examples_failed for r in results),
        "failed_files": [asdict(r) for r in results if not r.ok][:30],
        "results": [asdict(r) for r in results],
    }
    payload["package_complete"] = payload["file_count"] == spec.TASK_COUNT and payload["missing_task_count"] == 0
    payload["ok_for_submission_queue"] = (
        payload["package_complete"]
        and payload["all_structural_ok"]
        and payload["examples_failed"] == 0
        and not payload["has_duplicates"]
    )
    return payload


def write_validation(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
