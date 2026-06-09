from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml

from . import spec
from .data_io import iter_pairs, load_task, pair_to_numpy
from .evidence_gate import parse_evidence_registry


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def weighted_score(values: dict[str, float], weights: dict[str, float]) -> float:
    total = sum(float(weights.get(key, 0.0)) for key in values)
    if total <= 0:
        return 0.0
    return clamp(
        sum(float(values[key]) * float(weights.get(key, 0.0)) for key in values)
        / total
    )


def normalized_counter_delta(left: Counter, right: Counter) -> float:
    keys = set(left) | set(right)
    total = sum(left.values()) + sum(right.values())
    if not keys or total == 0:
        return 0.0
    return clamp(sum(abs(left[key] - right[key]) for key in keys) / total)


def tensor_bytes(tensor) -> int:
    import onnx

    if tensor.raw_data:
        return len(tensor.raw_data)
    width = {
        onnx.TensorProto.FLOAT: 4,
        onnx.TensorProto.UINT8: 1,
        onnx.TensorProto.INT8: 1,
        onnx.TensorProto.UINT16: 2,
        onnx.TensorProto.INT16: 2,
        onnx.TensorProto.INT32: 4,
        onnx.TensorProto.INT64: 8,
        onnx.TensorProto.BOOL: 1,
        onnx.TensorProto.FLOAT16: 2,
        onnx.TensorProto.DOUBLE: 8,
        onnx.TensorProto.UINT32: 4,
        onnx.TensorProto.UINT64: 8,
        onnx.TensorProto.BFLOAT16: 2,
    }.get(tensor.data_type, 4)
    count = math.prod(tensor.dims) if tensor.dims else 1
    return int(count * width)


def op_family(op_type: str) -> str:
    op = op_type.upper()
    groups = {
        "CONV": "linear",
        "MATMUL": "linear",
        "GEMM": "linear",
        "ADD": "arithmetic",
        "SUB": "arithmetic",
        "MUL": "arithmetic",
        "DIV": "arithmetic",
        "MOD": "arithmetic",
        "EQUAL": "comparison",
        "GREATER": "comparison",
        "LESS": "comparison",
        "WHERE": "selection",
        "GATHER": "indexing",
        "GATHERND": "indexing",
        "SLICE": "indexing",
        "SCATTERND": "indexing",
        "RESHAPE": "shape",
        "TRANSPOSE": "shape",
        "SQUEEZE": "shape",
        "UNSQUEEZE": "shape",
        "CONCAT": "shape",
        "REDUCEMAX": "reduction",
        "REDUCESUM": "reduction",
        "ARGMAX": "reduction",
        "CAST": "dtype",
        "CONSTANT": "constant",
    }
    return groups.get(op, op.lower())


def graph_signature(path: Path, wl_iterations: int, path_depth: int) -> dict:
    import onnx

    model = onnx.load(str(path), load_external_data=False)
    nodes = list(model.graph.node)
    producer: dict[str, int] = {}
    consumers: dict[str, list[int]] = defaultdict(list)
    for index, node in enumerate(nodes):
        for output in node.output:
            producer[output] = index
        for input_name in node.input:
            consumers[input_name].append(index)

    edges: list[tuple[int, int]] = []
    successors: dict[int, set[int]] = defaultdict(set)
    predecessors: dict[int, set[int]] = defaultdict(set)
    for name, source in producer.items():
        for target in consumers.get(name, []):
            edges.append((source, target))
            successors[source].add(target)
            predecessors[target].add(source)

    op_counts = Counter(node.op_type for node in nodes)
    family_counts = Counter(op_family(node.op_type) for node in nodes)
    degree_counts = Counter(
        (len(predecessors[index]), len(successors[index]))
        for index in range(len(nodes))
    )
    labels = {
        index: f"{op_family(node.op_type)}:{len(node.input)}:{len(node.output)}"
        for index, node in enumerate(nodes)
    }
    wl_counts = Counter(labels.values())
    for _ in range(wl_iterations):
        next_labels: dict[int, str] = {}
        for index in range(len(nodes)):
            neighborhood = sorted(
                labels[item]
                for item in predecessors[index] | successors[index]
            )
            raw = labels[index] + "|" + "|".join(neighborhood)
            next_labels[index] = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
        labels = next_labels
        wl_counts.update(labels.values())

    path_counts: Counter = Counter()
    for start in range(len(nodes)):
        frontier = [(start, (op_family(nodes[start].op_type),))]
        for _ in range(path_depth - 1):
            next_frontier = []
            for node_index, path_ops in frontier:
                for successor in successors[node_index]:
                    new_path = path_ops + (op_family(nodes[successor].op_type),)
                    path_counts[new_path] += 1
                    next_frontier.append((successor, new_path))
            frontier = next_frontier

    initializer_bytes = sum(tensor_bytes(item) for item in model.graph.initializer)
    initializer_shapes = Counter(
        (item.data_type, tuple(item.dims)) for item in model.graph.initializer
    )
    value_info_count = (
        len(model.graph.value_info)
        + len(model.graph.input)
        + len(model.graph.output)
    )
    activation_proxy = max(1, len(nodes)) * max(1, value_info_count) * 16
    memory_proxy = initializer_bytes + activation_proxy
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "op_counts": op_counts,
        "family_counts": family_counts,
        "degree_counts": degree_counts,
        "wl_counts": wl_counts,
        "path_counts": path_counts,
        "initializer_count": len(model.graph.initializer),
        "initializer_bytes": initializer_bytes,
        "initializer_shapes": initializer_shapes,
        "memory_proxy": memory_proxy,
    }


def topology_delta(base: dict, candidate: dict) -> float:
    size_delta = (
        abs(base["node_count"] - candidate["node_count"])
        + abs(base["edge_count"] - candidate["edge_count"])
    ) / max(
        1,
        base["node_count"]
        + candidate["node_count"]
        + base["edge_count"]
        + candidate["edge_count"],
    )
    degree_delta = normalized_counter_delta(
        base["degree_counts"], candidate["degree_counts"]
    )
    return clamp(0.55 * size_delta + 0.45 * degree_delta)


def initializer_delta(base: dict, candidate: dict) -> float:
    numeric = (
        abs(base["initializer_count"] - candidate["initializer_count"])
        + abs(base["initializer_bytes"] - candidate["initializer_bytes"])
        / max(1, max(base["initializer_bytes"], candidate["initializer_bytes"]))
    ) / 2
    shape_delta = normalized_counter_delta(
        base["initializer_shapes"], candidate["initializer_shapes"]
    )
    return clamp(0.55 * numeric + 0.45 * shape_delta)


def rewrite_class_score(base: dict, candidate: dict) -> tuple[float, list[str]]:
    classes: list[str] = []
    score = 0.0
    if candidate["node_count"] < base["node_count"] * 0.8:
        classes.append("node_pruning_or_fusion")
        score += 0.25
    if candidate["initializer_bytes"] < base["initializer_bytes"] * 0.75:
        classes.append("initializer_elimination")
        score += 0.25
    if normalized_counter_delta(base["family_counts"], candidate["family_counts"]) > 0.2:
        classes.append("operator_family_rewrite")
        score += 0.25
    if topology_delta(base, candidate) > 0.2:
        classes.append("topology_rewrite")
        score += 0.25
    return clamp(score), classes or ["model_substitution"]


def changed_tasks(manifest: dict, candidate_dir: Path) -> list[str]:
    tasks = manifest.get("changed_tasks", [])
    if isinstance(tasks, str):
        return [item for item in tasks.split(",") if item]
    if tasks:
        return list(tasks)
    changed_path = candidate_dir / "changed_tasks.csv"
    if changed_path.exists():
        with changed_path.open(newline="", encoding="utf-8") as handle:
            return [row["task_id"] for row in csv.DictReader(handle)]
    return []


def differential_output_consistency(
    *,
    root: Path,
    base_dir: Path,
    candidate_dir: Path,
    tasks: list[str],
    max_tasks: int,
    examples_per_task: int,
) -> dict:
    import numpy as np
    import onnx
    import onnxruntime as ort

    checked = matched = optimized_matched = expected_passed = errors = 0
    data_dir = root / "data/raw/neurogolf-2026"
    for task_id in tasks[:max_tasks]:
        base_model = base_dir / f"{task_id}.onnx"
        candidate_model = candidate_dir / f"{task_id}.onnx"
        task_path = data_dir / f"{task_id}.json"
        if not base_model.exists() or not candidate_model.exists() or not task_path.exists():
            continue
        try:
            base_proto = onnx.load(str(base_model), load_external_data=False)
            candidate_proto = onnx.load(str(candidate_model), load_external_data=False)
            disabled = ort.SessionOptions()
            disabled.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
            disabled.log_severity_level = 3
            enabled = ort.SessionOptions()
            enabled.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            enabled.log_severity_level = 3
            base_session = ort.InferenceSession(
                base_proto.SerializeToString(),
                disabled,
                providers=["CPUExecutionProvider"],
            )
            candidate_disabled = ort.InferenceSession(
                candidate_proto.SerializeToString(),
                disabled,
                providers=["CPUExecutionProvider"],
            )
            candidate_enabled = ort.InferenceSession(
                candidate_proto.SerializeToString(),
                enabled,
                providers=["CPUExecutionProvider"],
            )
            used = 0
            for _, pair in iter_pairs(load_task(task_path)):
                if used >= examples_per_task:
                    break
                arrays = pair_to_numpy(pair)
                if arrays is None:
                    continue
                used += 1
                checked += 1
                x, expected = arrays
                base_output = base_session.run(
                    [spec.OUTPUT_NAME], {spec.INPUT_NAME: x}
                )[0]
                candidate_output = candidate_disabled.run(
                    [spec.OUTPUT_NAME], {spec.INPUT_NAME: x}
                )[0]
                optimized_output = candidate_enabled.run(
                    [spec.OUTPUT_NAME], {spec.INPUT_NAME: x}
                )[0]
                base_binary = base_output > 0.0
                candidate_binary = candidate_output > 0.0
                optimized_binary = optimized_output > 0.0
                expected_binary = expected > 0.0
                matched += int(np.array_equal(base_binary, candidate_binary))
                optimized_matched += int(
                    np.array_equal(candidate_binary, optimized_binary)
                )
                expected_passed += int(
                    np.array_equal(candidate_binary, expected_binary)
                )
        except Exception:
            errors += 1
    if not checked:
        return {
            "score": 0.0,
            "checked": 0,
            "base_candidate_matches": 0,
            "optimizer_level_matches": 0,
            "expected_passes": 0,
            "errors": errors,
        }
    return {
        "score": clamp(
            0.40 * (matched / checked)
            + 0.35 * (optimized_matched / checked)
            + 0.25 * (expected_passed / checked)
        ),
        "checked": checked,
        "base_candidate_matches": matched,
        "optimizer_level_matches": optimized_matched,
        "expected_passes": expected_passed,
        "errors": errors,
    }


def validation_components(
    candidate_dir: Path,
    changed_tasks: list[str],
    differential: dict,
) -> dict[str, float]:
    path = candidate_dir / "local_validation.json"
    if not path.exists():
        return {
            "local_example_pass": 0.0,
            "structural_legality": 0.0,
            "differential_output_consistency": 0.0,
            "operator_conformance": 0.0,
            "hidden_generalization_proxy": 0.0,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    checked = int(data.get("examples_checked", 0))
    passed = int(data.get("examples_passed", 0))
    local_pass = passed / checked if checked else 0.0
    structural = 1.0 if data.get("all_structural_ok") else 0.0
    changed = set(changed_tasks)
    results = [
        item
        for item in data.get("results", [])
        if not changed or item.get("task_id") in changed
    ]
    legal_results = sum(not item.get("structural_errors") for item in results)
    operator_conformance = legal_results / len(results) if results else 0.0
    package_complete = 1.0 if (
        data.get("package_complete")
        or (
            int(data.get("file_count", 0))
            == int(data.get("expected_task_count", 400))
            and int(data.get("missing_task_count", 0)) == 0
        )
    ) else 0.0
    differential_score = (
        float(differential["score"])
        if differential.get("checked")
        else clamp(0.55 * local_pass + 0.20 * package_complete)
    )
    changed_examples = sum(int(item.get("examples_checked", 0)) for item in results)
    hidden_proxy = clamp(
        local_pass
        * (0.55 + min(0.30, math.log10(max(10, changed_examples)) / 10))
        * (0.95 if len(changed_tasks) <= 5 else 0.82)
    )
    return {
        "local_example_pass": local_pass,
        "structural_legality": structural,
        "differential_output_consistency": differential_score,
        "operator_conformance": operator_conformance,
        "hidden_generalization_proxy": hidden_proxy,
    }


def claimed_score(registry_text: str, source_id: str) -> float:
    match = re.search(
        rf"(?ms)^source_id:\s*{re.escape(source_id)}\s*$.*?^claimed_score:\s*([0-9.]+)\s*$",
        registry_text,
    )
    return float(match.group(1)) if match else 0.0


def classify(
    final_score: float,
    *,
    structural_score: float,
    changed_task_count: int,
    content_changed_task_count: int,
    validation_ok: bool,
    evidence_status: str,
    config: dict,
) -> str:
    if evidence_status != "pass":
        return "evidence_gate_fail"
    if not validation_ok:
        return "validation_fail"
    if structural_score < 0.02:
        if changed_task_count >= 20 and content_changed_task_count >= 10:
            return "full_bundle_replacement"
        if content_changed_task_count >= 1 and final_score >= float(
            config["classification_thresholds"]["exploratory_submit"]
        ):
            return "exploratory_submit"
        return "metadata_only"
    thresholds = config["classification_thresholds"]
    if final_score >= float(thresholds["aggressive"]):
        return "aggressive"
    if final_score >= float(thresholds["strong"]):
        return "strong"
    if final_score >= float(thresholds["exploratory_submit"]):
        return "exploratory_submit"
    if final_score >= float(thresholds["manual_review"]):
        return "manual_review"
    return "low_value"


def score_candidate(root: Path, exp_id: str) -> dict:
    config = yaml.safe_load(
        (root / "configs/aggressive_change_score.yaml").read_text(encoding="utf-8")
    )
    candidate_dir = root / "submissions/candidates" / exp_id
    manifest_path = candidate_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing candidate manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_path = Path(manifest.get("base", ""))
    if not base_path.is_absolute():
        base_path = root / base_path
    base_dir = base_path / "onnx" if (base_path / "onnx").exists() else base_path
    candidate_onnx = candidate_dir / "onnx"
    tasks = changed_tasks(manifest, candidate_dir)

    structural_parts = Counter()
    rewrite_classes = Counter()
    base_memory = 0
    candidate_memory = 0
    scored_tasks = 0
    content_changed_tasks: list[str] = []
    for task_id in tasks:
        base_model = base_dir / f"{task_id}.onnx"
        candidate_model = candidate_onnx / f"{task_id}.onnx"
        if not base_model.exists() or not candidate_model.exists():
            continue
        if hashlib.sha256(base_model.read_bytes()).hexdigest() != hashlib.sha256(
            candidate_model.read_bytes()
        ).hexdigest():
            content_changed_tasks.append(task_id)
        base = graph_signature(
            base_model, int(config["wl_iterations"]), int(config["dataflow_path_depth"])
        )
        candidate = graph_signature(
            candidate_model,
            int(config["wl_iterations"]),
            int(config["dataflow_path_depth"]),
        )
        rewrite_score, classes = rewrite_class_score(base, candidate)
        task_parts = {
            "op_family_delta": normalized_counter_delta(
                base["family_counts"], candidate["family_counts"]
            ),
            "topology_delta": topology_delta(base, candidate),
            "wl_subgraph_delta": normalized_counter_delta(
                base["wl_counts"], candidate["wl_counts"]
            ),
            "dataflow_path_delta": normalized_counter_delta(
                base["path_counts"], candidate["path_counts"]
            ),
            "initializer_structure_delta": initializer_delta(base, candidate),
            "memory_profile_delta": clamp(
                abs(base["memory_proxy"] - candidate["memory_proxy"])
                / max(1, max(base["memory_proxy"], candidate["memory_proxy"]))
            ),
            "rewrite_class_score": rewrite_score,
        }
        structural_parts.update(task_parts)
        rewrite_classes.update(classes)
        base_memory += base["memory_proxy"]
        candidate_memory += candidate["memory_proxy"]
        scored_tasks += 1

    if scored_tasks:
        structural_components = {
            key: structural_parts[key] / scored_tasks
            for key in config["structural_delta_weights"]
        }
    else:
        structural_components = {
            key: 0.0 for key in config["structural_delta_weights"]
        }
    structural_score = weighted_score(
        structural_components, config["structural_delta_weights"]
    )

    differential = differential_output_consistency(
        root=root,
        base_dir=base_dir,
        candidate_dir=candidate_onnx,
        tasks=tasks,
        max_tasks=int(config.get("differential_max_tasks", 24)),
        examples_per_task=int(config.get("differential_examples_per_task", 3)),
    )
    semantic_components = validation_components(candidate_dir, tasks, differential)
    semantic_score = weighted_score(
        semantic_components, config["semantic_validity_weights"]
    )

    registry_text = (root / "research/EVIDENCE_REGISTRY.md").read_text(
        encoding="utf-8"
    )
    source_score = claimed_score(
        registry_text, manifest.get("leaderboard_source_id", "")
    )
    bottom_tasks = set(config["bottom_tail_tasks"])
    bottom_overlap = len(bottom_tasks & set(tasks)) / max(1, len(bottom_tasks))
    memory_gain = clamp(
        (base_memory - candidate_memory) / max(1, base_memory)
    )
    queue_path = root / "experiments/submission_queue.csv"
    submitted = False
    if queue_path.exists():
        with queue_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("exp_id") == exp_id:
                    submitted = row.get("submitted", "").lower() == "true"
                    break
    competition_components = {
        "source_lb_strength": clamp(source_score / 7000.0)
        if source_score
        else 0.55,
        "affected_task_importance": clamp(
            0.35 + 0.45 * bottom_overlap + 0.20 * min(1.0, len(tasks) / 50)
        ),
        "expected_memory_gain": memory_gain,
        "bottom_tail_relevance": bottom_overlap,
        "submission_feedback_need": 0.25 if submitted else 1.0,
    }
    competition_score = weighted_score(
        competition_components, config["competition_value_weights"]
    )

    evidence_sources = parse_evidence_registry(
        root / "research/EVIDENCE_REGISTRY.md"
    )
    evidence_status = manifest.get("evidence_gate_status", "")
    novelty_components = {
        "graph_novelty": structural_score,
        "leaderboard_basis": 1.0
        if manifest.get("leaderboard_source_id") in evidence_sources
        else 0.0,
        "paper_basis": 1.0
        if manifest.get("paper_source_id") in evidence_sources
        else 0.0,
        "open_repo_basis": 1.0
        if manifest.get("open_repo_source_id") in evidence_sources
        else 0.0,
        "historical_competition_basis": 1.0
        if manifest.get("historical_competition_source_id") in evidence_sources
        else 0.0,
    }
    novelty_score = weighted_score(
        novelty_components, config["novelty_source_weights"]
    )
    layers = {
        "structural_delta": structural_score,
        "semantic_risk_adjusted_validity": semantic_score,
        "competition_value": competition_score,
        "novelty_and_source_strength": novelty_score,
    }
    final_score = weighted_score(layers, config["layer_weights"])
    validation_ok = bool(manifest.get("validation_ok"))
    classification = classify(
        final_score,
        structural_score=structural_score,
        changed_task_count=len(tasks),
        content_changed_task_count=len(content_changed_tasks),
        validation_ok=validation_ok,
        evidence_status=evidence_status,
        config=config,
    )
    hard_reject = classification in set(config["hard_reject_classifications"])
    calibration_allowed = (
        config.get("calibration_phase", False)
        and config.get("user_policy") == "aggressive"
        and classification in set(config.get("calibration_submit_classifications", []))
    )
    payload = {
        "exp_id": exp_id,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "base": str(base_path),
        "changed_task_count": len(tasks),
        "content_changed_task_count": len(content_changed_tasks),
        "content_changed_tasks": content_changed_tasks,
        "scored_task_count": scored_tasks,
        "evidence_gate_status": evidence_status,
        "risk": manifest.get("risk", ""),
        "layers": layers,
        "structural_delta_components": structural_components,
        "semantic_risk_adjusted_validity_components": semantic_components,
        "differential_testing": differential,
        "competition_value_components": competition_components,
        "novelty_and_source_strength_components": novelty_components,
        "memory_profile": {
            "base_proxy": base_memory,
            "candidate_proxy": candidate_memory,
            "expected_gain_ratio": memory_gain,
        },
        "rewrite_classes": dict(rewrite_classes),
        "ags": final_score,
        "classification": classification,
        "hard_reject": hard_reject,
        "calibration_submit_allowed": calibration_allowed,
        "submission_gate_pass": not hard_reject,
        "reference_basis": config.get("reference_basis", {}),
    }
    return payload


def write_score_outputs(root: Path, payload: dict) -> None:
    exp_id = payload["exp_id"]
    manifest_path = root / "data/manifests" / f"aggressive_change_{exp_id}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = root / "reports" / f"AGGRESSIVE_CHANGE_{exp_id}.md"
    lines = [
        f"# Aggressive Change: {exp_id}",
        "",
        f"checked_at: {payload['checked_at']}",
        f"AGS: {payload['ags']:.4f}",
        f"classification: {payload['classification']}",
        f"submission_gate_pass: {str(payload['submission_gate_pass']).lower()}",
        f"risk: {payload['risk']}",
        f"content_changed_task_count: {payload['content_changed_task_count']}",
        "",
        "## Layers",
        "",
    ]
    for key, value in payload["layers"].items():
        lines.append(f"- {key}: {value:.4f}")
    lines.extend(["", "## Structural Delta", ""])
    for key, value in payload["structural_delta_components"].items():
        lines.append(f"- {key}: {value:.4f}")
    lines.extend(["", "## Rewrite Classes", ""])
    if payload["rewrite_classes"]:
        for key, value in payload["rewrite_classes"].items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    lines.extend(["", "## Differential Testing", ""])
    for key, value in payload["differential_testing"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")

    csv_path = root / "task_bank/aggressive_change_scores.csv"
    fields = [
        "exp_id",
        "checked_at",
        "ags",
        "classification",
        "submission_gate_pass",
        "risk",
        "changed_task_count",
        "content_changed_task_count",
        "structural_delta",
        "semantic_risk_adjusted_validity",
        "competition_value",
        "novelty_and_source_strength",
    ]
    rows: list[dict] = []
    if csv_path.exists() and csv_path.stat().st_size:
        with csv_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    row = {
        "exp_id": exp_id,
        "checked_at": payload["checked_at"],
        "ags": f"{payload['ags']:.6f}",
        "classification": payload["classification"],
        "submission_gate_pass": str(payload["submission_gate_pass"]).lower(),
        "risk": payload["risk"],
        "changed_task_count": payload["changed_task_count"],
        "content_changed_task_count": payload["content_changed_task_count"],
        **{key: f"{value:.6f}" for key, value in payload["layers"].items()},
    }
    replaced = False
    for existing in rows:
        if existing.get("exp_id") == exp_id:
            existing.update(row)
            replaced = True
            break
    if not replaced:
        rows.append(row)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: item.get(key, "") for key in fields} for item in rows)

    status_path = root / "reports/AGGRESSIVE_CHANGE_SCORE_STATUS.md"
    status_lines = [
        "# Aggressive Change Score Status",
        "",
        f"last_updated: {payload['checked_at']}",
        "",
        "| exp_id | AGS | classification | gate | risk |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for item in rows:
        status_lines.append(
            f"| {item['exp_id']} | {item['ags']} | {item['classification']} | "
            f"{item['submission_gate_pass']} | {item['risk']} |"
        )
    status_lines.append("")
    status_path.write_text("\n".join(status_lines), encoding="utf-8")

    candidate_manifest = (
        root / "submissions/candidates" / exp_id / "manifest.json"
    )
    if candidate_manifest.exists():
        manifest = json.loads(candidate_manifest.read_text(encoding="utf-8"))
        manifest.update(
            {
                "aggressive_change_score": payload["ags"],
                "aggressive_change_classification": payload["classification"],
                "aggressive_change_checked_at": payload["checked_at"],
                "aggressive_change_gate_pass": payload["submission_gate_pass"],
                "aggressive_content_changed_task_count": payload[
                    "content_changed_task_count"
                ],
            }
        )
        candidate_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    queue_path = root / "experiments/submission_queue.csv"
    if queue_path.exists() and queue_path.stat().st_size:
        with queue_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            queue_rows = list(reader)
            queue_fields = list(reader.fieldnames or [])
        for field in [
            "aggressive_change_score",
            "aggressive_change_classification",
            "aggressive_change_gate_status",
        ]:
            if field not in queue_fields:
                queue_fields.append(field)
        for item in queue_rows:
            if item.get("exp_id") == exp_id:
                item["aggressive_change_score"] = f"{payload['ags']:.6f}"
                item["aggressive_change_classification"] = payload["classification"]
                item["aggressive_change_gate_status"] = (
                    "pass" if payload["submission_gate_pass"] else "fail"
                )
        with queue_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=queue_fields)
            writer.writeheader()
            writer.writerows(
                {key: item.get(key, "") for key in queue_fields}
                for item in queue_rows
            )
