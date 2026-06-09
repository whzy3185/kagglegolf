from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib
import inspect
import json
import sys
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.onnx_score import points


def canonical_hash(payload: dict) -> str:
    core = {"train": payload["train"], "test": payload["test"]}
    text = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_grid(value: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(cell) for cell in row) for row in value)


def solver_metrics(solver) -> tuple[int, int, str]:
    source = inspect.getsource(solver)
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    names = []
    for call in calls:
        if isinstance(call.func, ast.Name):
            names.append(call.func.id)
        elif isinstance(call.func, ast.Attribute):
            names.append(call.func.attr)
    return len(source.splitlines()), len(calls), ",".join(sorted(set(names)))


def build_arc_map(official_dir: Path, neurogolf_dir: Path) -> dict[str, str]:
    by_hash = {}
    for path in official_dir.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        by_hash[canonical_hash(payload)] = path.stem

    mapping = {}
    for path in sorted(neurogolf_dir.glob("task*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        arc_id = by_hash.get(canonical_hash(payload), "")
        mapping[path.stem] = arc_id
    return mapping


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def quick_model_profile(path: Path) -> dict:
    import numpy as np
    import onnx

    try:
        model = onnx.load(str(path))
        params = 0
        for init in model.graph.initializer:
            params += int(np.prod(init.dims)) if init.dims else 1
        for node in model.graph.node:
            if node.op_type != "Constant":
                continue
            for attr in node.attribute:
                if attr.name == "value":
                    params += int(np.prod(attr.t.dims)) if attr.t.dims else 1
        file_size = path.stat().st_size
        return {
            "node_count": len(model.graph.node),
            "cost_proxy": file_size + params,
            "utility_proxy": points(file_size, params),
        }
    except Exception:
        return {"node_count": 0, "cost_proxy": 0, "utility_proxy": 0.0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate-dir",
        default="submissions/candidates/GOLF_20260608_046_rogermt_positive_stack_255_128_208/onnx",
    )
    parser.add_argument("--arc-dsl-dir", default="external/arc_dsl")
    parser.add_argument("--arc-gen-limit", type=int, default=10)
    args = parser.parse_args()

    neurogolf_dir = ROOT / "data/raw/neurogolf-2026"
    official_dir = ROOT / "external/arc_agi_official/data/training"
    arc_dsl_dir = ROOT / args.arc_dsl_dir
    candidate_dir = ROOT / args.candidate_dir

    mapping = build_arc_map(official_dir, neurogolf_dir)
    if len(mapping) != 400 or any(not value for value in mapping.values()):
        raise SystemExit("ARC task mapping is incomplete")

    sys.path.insert(0, str(arc_dsl_dir))
    solvers = importlib.import_module("solvers")

    rows = []
    for task_id, arc_id in mapping.items():
        payload = json.loads((neurogolf_dir / f"{task_id}.json").read_text(encoding="utf-8"))
        solver_name = f"solve_{arc_id}"
        solver = getattr(solvers, solver_name, None)
        line_count = call_count = 0
        primitives = ""
        if solver is not None:
            line_count, call_count, primitives = solver_metrics(solver)

        split_counts = {}
        errors = []
        total_pass = 0
        total_examples = 0
        for split in ("train", "test", "arc-gen"):
            examples = payload.get(split, [])
            if split == "arc-gen" and args.arc_gen_limit:
                examples = examples[: args.arc_gen_limit]
            passed = 0
            for index, example in enumerate(examples):
                total_examples += 1
                try:
                    output = solver(as_grid(example["input"])) if solver else None
                    if output == as_grid(example["output"]):
                        passed += 1
                        total_pass += 1
                    else:
                        errors.append(f"{split}[{index}]:output_mismatch")
                except Exception as exc:
                    errors.append(f"{split}[{index}]:{type(exc).__name__}")
            split_counts[split] = (passed, len(examples))

        model_path = candidate_dir / f"{task_id}.onnx"
        profile = quick_model_profile(model_path)
        official_pass = (
            split_counts["train"][0] == split_counts["train"][1]
            and split_counts["test"][0] == split_counts["test"][1]
        )
        arc_gen_pass = split_counts["arc-gen"][0] == split_counts["arc-gen"][1]
        rows.append(
            {
                "task_id": task_id,
                "arc_id": arc_id,
                "solver_name": solver_name,
                "solver_exists": str(solver is not None).lower(),
                "solver_lines": line_count,
                "dsl_call_count": call_count,
                "dsl_primitives": primitives,
                "train_pass": split_counts["train"][0],
                "train_total": split_counts["train"][1],
                "test_pass": split_counts["test"][0],
                "test_total": split_counts["test"][1],
                "arc_gen_pass": split_counts["arc-gen"][0],
                "arc_gen_total": split_counts["arc-gen"][1],
                "official_pass": str(official_pass).lower(),
                "all_examples_pass": str(official_pass and arc_gen_pass).lower(),
                "current_node_count": profile["node_count"],
                "current_cost_proxy": profile["cost_proxy"],
                "current_utility_proxy": f"{profile['utility_proxy']:.6f}",
                "compile_priority": (
                    (25.0 - float(profile["utility_proxy"])) / max(call_count, 1)
                    if official_pass
                    else 0.0
                ),
                "errors": ";".join(errors[:8]),
            }
        )
        if len(rows) % 50 == 0:
            print(f"audited={len(rows)}/400", flush=True)

    rows.sort(key=lambda row: float(row["compile_priority"]), reverse=True)
    write_csv(ROOT / "task_bank/arc_dsl_solver_audit.csv", rows)
    (ROOT / "data/manifests/neurogolf_arc_training_map.json").write_text(
        json.dumps(mapping, indent=2),
        encoding="utf-8",
    )

    official_pass_count = sum(row["official_pass"] == "true" for row in rows)
    all_pass_count = sum(row["all_examples_pass"] == "true" for row in rows)
    top = rows[:30]
    report = [
        "# ARC-DSL Solver Audit",
        "",
        f"checked_at: {datetime.now().isoformat(timespec='seconds')}",
        f"mapped_tasks: {len(mapping)}/400",
        f"official_train_test_pass: {official_pass_count}/400",
        f"official_plus_arc_gen_pass: {all_pass_count}/400",
        f"candidate_dir: {args.candidate_dir}",
        "",
        "## Architecture Decision",
        "",
        "NeuroGolf task numbering maps exactly to the public ARC-AGI training set.",
        "Use ARC-DSL programs as task-level solver specifications and compile the",
        "highest-loss, shortest programs into compact ONNX graphs.",
        "",
        "## Top Compile Priorities",
        "",
        "| task | ARC id | DSL calls | current utility | priority | all examples |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in top:
        report.append(
            f"| {row['task_id']} | {row['arc_id']} | {row['dsl_call_count']} | "
            f"{row['current_utility_proxy']} | {float(row['compile_priority']):.4f} | "
            f"{row['all_examples_pass']} |"
        )
    (ROOT / "reports/ARC_DSL_SOLVER_AUDIT.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )
    print(f"mapped_tasks={len(mapping)}")
    print(f"official_train_test_pass={official_pass_count}")
    print(f"official_plus_arc_gen_pass={all_pass_count}")
    print("report=reports/ARC_DSL_SOLVER_AUDIT.md")


if __name__ == "__main__":
    main()
