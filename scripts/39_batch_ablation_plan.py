from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.paths import root
from neurogolf.simple_exact import write_csv


RESULT_FIELDS = [
    "exp_id",
    "created_at",
    "base_exp_id",
    "changed_task_count",
    "changed_tasks",
    "rule_names",
    "status",
    "submission_id",
    "public_score",
    "score_delta_vs_parent",
    "outcome",
    "ablation_needed",
    "child_exp_ids",
    "notes",
]


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists() or not path.stat().st_size:
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def fnum(value: object) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except ValueError:
        return None


def complete(status: str) -> bool:
    return "complete" in status.lower()


def manifest(exp_id: str) -> dict:
    path = root("submissions/candidates", exp_id, "manifest.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def queue_rows() -> list[dict]:
    return read_csv(root("experiments/submission_queue.csv"))[1]


def task_signature(base_exp_id: str, tasks: list[str]) -> tuple[str, tuple[str, ...]]:
    return base_exp_id, tuple(tasks)


def signature_index(rows: list[dict]) -> dict[tuple[str, tuple[str, ...]], str]:
    index: dict[tuple[str, tuple[str, ...]], str] = {}
    for row in rows:
        exp_id = row.get("exp_id", "")
        if "simple_exact_batch" not in exp_id:
            continue
        payload = manifest(exp_id)
        tasks = payload.get("changed_tasks") or [
            item.strip() for item in row.get("changed_tasks", "").split(",") if item.strip()
        ]
        base_exp_id = payload.get("base_exp_id") or payload.get("parent_exp_id") or ""
        if base_exp_id and tasks:
            index.setdefault(task_signature(base_exp_id, tasks), exp_id)
    return index


def exp_number(exp_id: str) -> int:
    match = re.search(r"GOLF_\d{8}_(\d+)_", exp_id)
    return int(match.group(1)) if match else 0


def exp_date(exp_id: str) -> str:
    match = re.search(r"GOLF_(\d{8})_", exp_id)
    return match.group(1) if match else datetime.now().strftime("%Y%m%d")


def child_ids(parent: str, task_count: int) -> tuple[str, str]:
    date = exp_date(parent)
    number = exp_number(parent)
    parent_label = f"{number:03d}" if number else "parent"
    left = task_count // 2
    right = task_count - left
    return (
        f"GOLF_{date}_{number + 1:03d}_simple_exact_batch_{parent_label}_A{left}",
        f"GOLF_{date}_{number + 2:03d}_simple_exact_batch_{parent_label}_B{right}",
    )


def child_exists(exp_id: str) -> bool:
    if root("submissions/candidates", exp_id).exists():
        return True
    return any(row.get("exp_id") == exp_id for row in queue_rows())


def write_task_list(exp_id: str, tasks: list[str]) -> Path:
    path = root("task_bank", f"{exp_id}.txt")
    path.write_text("\n".join(tasks) + "\n", encoding="utf-8")
    return path


def build_child(base_exp_id: str, child_exp_id: str, tasks: list[str]) -> tuple[int, str]:
    task_list = write_task_list(child_exp_id, tasks)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/38_build_multitask_replacement.py",
            "--base-exp-id",
            base_exp_id,
            "--task-list",
            str(task_list),
            "--exp-id",
            child_exp_id,
            "--max-tasks",
            str(len(tasks)),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, ((result.stdout or "") + (result.stderr or "")).strip()[:1000]


def classify(row: dict) -> tuple[str, bool]:
    if not row.get("public_score") or not complete(row.get("status", "")):
        return "pending_or_unscored", False
    delta = fnum(row.get("score_delta_vs_parent"))
    if delta is None:
        return "score_without_parent_delta", False
    if delta > 0.0001:
        return "positive_batch", False
    if delta < -0.0001:
        return "negative_batch", True
    return "neutral_batch", False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    queue = queue_rows()
    signatures = signature_index(queue)
    existing_results = read_csv(root("task_bank/simple_exact_batch_results.csv"))[1]
    existing_by_exp = {row.get("exp_id", ""): row for row in existing_results}
    result_rows: list[dict] = []
    build_logs: list[str] = []
    positive: list[str] = []
    negative: list[str] = []
    pending: list[str] = []
    ablation_needed: list[str] = []

    for row in queue:
        exp_id = row.get("exp_id", "")
        if "simple_exact_batch" not in exp_id:
            continue
        payload = manifest(exp_id)
        tasks = payload.get("changed_tasks") or [
            item.strip() for item in row.get("changed_tasks", "").split(",") if item.strip()
        ]
        rule_names = payload.get("rule_name_list") or []
        outcome, needs_ablation = classify(row)
        if outcome == "positive_batch":
            positive.append(exp_id)
        elif outcome == "negative_batch":
            negative.append(exp_id)
        else:
            pending.append(exp_id)
        child_pair = ("", "")
        notes = "no ablation action"
        if needs_ablation and len(tasks) > 1:
            child_pair = child_ids(exp_id, len(tasks))
            ablation_needed.append(exp_id)
            left_count = len(tasks) // 2
            left_tasks = tasks[:left_count]
            right_tasks = tasks[left_count:]
            notes = f"split into {child_pair[0]} and {child_pair[1]}"
            base_exp_id = payload.get("base_exp_id") or payload.get("parent_exp_id") or ""
            if base_exp_id and not args.no_build:
                for child_exp_id, child_tasks in [(child_pair[0], left_tasks), (child_pair[1], right_tasks)]:
                    duplicate_of = signatures.get(task_signature(base_exp_id, child_tasks))
                    if duplicate_of and duplicate_of != child_exp_id:
                        build_logs.append(
                            f"{child_exp_id}: duplicate task set of {duplicate_of}; skipped"
                        )
                        continue
                    if child_exists(child_exp_id):
                        build_logs.append(f"{child_exp_id}: already exists")
                        continue
                    code, text = build_child(base_exp_id, child_exp_id, child_tasks)
                    build_logs.append(f"{child_exp_id}: returncode={code}; {text}")
                    if code == 0:
                        signatures[task_signature(base_exp_id, child_tasks)] = child_exp_id
        elif needs_ablation:
            ablation_needed.append(exp_id)
            notes = "negative single-task batch cannot be split further"

        base_existing = existing_by_exp.get(exp_id, {})
        result_rows.append(
            {
                "exp_id": exp_id,
                "created_at": base_existing.get("created_at") or datetime.now().isoformat(timespec="seconds"),
                "base_exp_id": payload.get("base_exp_id", ""),
                "changed_task_count": len(tasks),
                "changed_tasks": ",".join(tasks),
                "rule_names": ",".join(rule_names),
                "status": row.get("status", ""),
                "submission_id": row.get("submission_id", ""),
                "public_score": row.get("public_score", ""),
                "score_delta_vs_parent": row.get("score_delta_vs_parent", ""),
                "outcome": outcome,
                "ablation_needed": str(needs_ablation).lower(),
                "child_exp_ids": ",".join(item for item in child_pair if item),
                "notes": notes,
            }
        )

    result_rows.sort(key=lambda item: item["exp_id"])
    write_csv(root("task_bank/simple_exact_batch_results.csv"), RESULT_FIELDS, result_rows)

    lines = [
        "# Batch Ablation Plan",
        "",
        f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"positive_batch_count: {len(positive)}",
        f"negative_batch_count: {len(negative)}",
        f"pending_or_unscored_count: {len(pending)}",
        f"ablation_needed_count: {len(ablation_needed)}",
        "",
        "## Batch Outcomes",
        "",
        "| exp_id | tasks | score | delta_parent | outcome | child_exp_ids |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in result_rows:
        lines.append(
            f"| {row['exp_id']} | {row['changed_task_count']} | {row['public_score']} | "
            f"{row['score_delta_vs_parent']} | {row['outcome']} | {row['child_exp_ids']} |"
        )
    if not result_rows:
        lines.append("| none | 0 |  |  | none |  |")
    lines.extend(["", "## Positive Batch", ""])
    lines.extend(f"- {item}" for item in positive) if positive else lines.append("None.")
    lines.extend(["", "## Negative Batch", ""])
    lines.extend(f"- {item}" for item in negative) if negative else lines.append("None.")
    lines.extend(["", "## Need Binary Ablation", ""])
    lines.extend(f"- {item}" for item in ablation_needed) if ablation_needed else lines.append("None.")
    lines.extend(["", "## Build Log", ""])
    lines.extend(f"- {item}" for item in build_logs) if build_logs else lines.append("No child candidates built in this run.")
    lines.append("")
    root("reports/BATCH_ABLATION_PLAN.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"positive_batch_count={len(positive)}")
    print(f"negative_batch_count={len(negative)}")
    print(f"ablation_needed_count={len(ablation_needed)}")


if __name__ == "__main__":
    main()
