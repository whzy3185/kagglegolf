from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.paths import root


ATTRIBUTION_FIELDS = [
    "exp_id",
    "task_id",
    "base_exp_id",
    "source_id",
    "changed_task_count",
    "submission_id",
    "public_score",
    "delta_vs_best",
    "delta_vs_parent",
    "attribution_strength",
    "decision",
    "keep_in_normal_bank",
    "keep_in_high_risk_bank",
    "notes",
]


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def number(value: object) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists() or not path.stat().st_size:
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def history() -> tuple[dict[str, dict], float]:
    path = root("data/manifests/kaggle_submission_history.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_exp: dict[str, dict] = {}
    for item in payload.get("rows", []):
        exp_id = str(item.get("description", "")).split("|", 1)[0].strip()
        if exp_id:
            by_exp[exp_id] = item
    best = number((payload.get("best_public") or {}).get("publicScore")) or 0.0
    return by_exp, best


def candidate_manifest(row: dict) -> dict:
    candidate = Path(str(row.get("candidate_path", "")))
    if not candidate.exists():
        candidate = root("submissions/candidates", row.get("exp_id", ""))
    path = candidate / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def parent_exp_id(manifest: dict) -> str:
    explicit = str(manifest.get("parent_exp_id", "")).strip()
    if explicit:
        return explicit
    base = str(manifest.get("base", "")).replace("\\", "/").rstrip("/")
    return base.rsplit("/", 1)[-1] if base else ""


def task_list(row: dict, manifest: dict) -> list[str]:
    tasks = manifest.get("changed_tasks")
    if isinstance(tasks, list) and tasks:
        return [str(item) for item in tasks]
    return [
        item.strip()
        for item in str(row.get("changed_tasks", "")).split(",")
        if item.strip()
    ]


def classify(
    *,
    count: int,
    delta_parent: float | None,
    risk: str,
) -> tuple[str, str, bool, bool, str]:
    high_risk = risk.lower() == "high"
    delta = delta_parent if delta_parent is not None else 0.0
    keep_normal = False
    keep_high = high_risk
    if count == 1:
        strength = "strong"
        if delta > 0.0001:
            decision = "confirmed_win"
            keep_normal = not high_risk
            notes = "Single-task positive delta; eligible for normal bank only outside high-risk lane."
        elif delta < -0.0001:
            decision = "rejected_for_current_base"
            notes = "Single-task probe scored below its parent base."
        else:
            decision = "neutral_probe"
            notes = "Single-task probe tied its parent; retain as alternate evidence."
    elif count <= 5:
        strength = "suspected"
        if delta > 0.0001:
            decision = "suspected_mix_win"
        elif delta < -0.0001:
            decision = "negative_or_mixed"
        else:
            decision = "neutral_small_mix"
        notes = "Small-mix result cannot be assigned to individual tasks without follow-up probes."
    elif count > 20:
        strength = "bundle_only"
        if delta > 0.0001:
            decision = "bundle_win"
        elif delta < -0.0001:
            decision = "bundle_negative"
        else:
            decision = "bundle_tie"
        notes = "Broad/full result is bundle-level evidence and cannot update per-task best records."
    else:
        strength = "weak"
        decision = "multi_task_unresolved"
        notes = "Medium-size mix requires narrower probes before task-level promotion."
    return strength, decision, keep_normal, keep_high, notes


def attribution_rows(
    queue_row: dict,
    *,
    history_by_exp: dict[str, dict],
    best_score: float,
) -> list[dict]:
    exp_id = queue_row.get("exp_id", "")
    hist = history_by_exp.get(exp_id)
    if not hist:
        return []
    score = number(hist.get("publicScore"))
    if score is None or "complete" not in str(hist.get("status", "")).lower():
        return []
    manifest = candidate_manifest(queue_row)
    tasks = task_list(queue_row, manifest)
    count = len(tasks)
    parent = parent_exp_id(manifest)
    parent_score = number((history_by_exp.get(parent) or {}).get("publicScore"))
    delta_best = score - best_score
    delta_parent = score - parent_score if parent_score is not None else None
    strength, decision, keep_normal, keep_high, notes = classify(
        count=count,
        delta_parent=delta_parent,
        risk=str(queue_row.get("risk", "")),
    )
    record_tasks = tasks if count <= 5 else [f"bundle_{count}_tasks"]
    return [
        {
            "exp_id": exp_id,
            "task_id": task,
            "base_exp_id": parent,
            "source_id": queue_row.get("source_id", ""),
            "changed_task_count": count,
            "submission_id": hist.get("ref", ""),
            "public_score": f"{score:.2f}",
            "delta_vs_best": f"{delta_best:.6f}",
            "delta_vs_parent": (
                f"{delta_parent:.6f}" if delta_parent is not None else ""
            ),
            "attribution_strength": strength,
            "decision": decision,
            "keep_in_normal_bank": str(keep_normal).lower(),
            "keep_in_high_risk_bank": str(keep_high).lower(),
            "notes": notes,
        }
        for task in record_tasks
    ]


def update_best_by_task(attributions: list[dict]) -> None:
    path = root("task_bank/best_by_task.csv")
    fields, rows = read_csv(path)
    by_task = {row.get("task_id", ""): row for row in rows}
    for item in attributions:
        if item["task_id"].startswith("bundle_"):
            exp_id = item["exp_id"]
            for existing in rows:
                if existing.get("last_changed_exp_id") == exp_id:
                    task_id = existing.get("task_id", "")
                    baseline_model = root(
                        "submissions/candidates",
                        "GOLF_20260607_001_public_6154_repro",
                        "onnx",
                        f"{task_id}.onnx",
                    )
                    existing.update(
                        {
                            "best_model_path": str(baseline_model),
                            "source_id": "SRC_KAGGLE_NOTEBOOK_OCTAVIO_6154",
                            "method": "public_6154_baseline",
                            "local_correct": "true",
                            "lb_delta_if_known": "0.000000",
                            "last_changed_exp_id": "GOLF_20260607_001_public_6154_repro",
                            "status": "confirmed_baseline",
                            "notes": (
                                f"Restored after {exp_id} produced "
                                f"{item['decision']} without task-level attribution."
                            ),
                        }
                    )
            continue
        existing = by_task.get(item["task_id"])
        if not existing or existing.get("last_changed_exp_id") != item["exp_id"]:
            continue
        if item["keep_in_normal_bank"] == "true":
            existing["status"] = "confirmed_lb_win"
            existing["lb_delta_if_known"] = item["delta_vs_parent"]
        else:
            existing["status"] = "alternate_not_promoted"
            existing["lb_delta_if_known"] = item["delta_vs_parent"]
            existing["notes"] = item["decision"]
    if fields:
        write_csv(path, fields, rows)


def write_report(rows: list[dict]) -> None:
    lines = [
        "# Task Attribution",
        "",
        f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| exp_id | task/bundle | count | score | delta parent | strength | decision | normal bank | high-risk bank |",
        "|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['exp_id']} | {row['task_id']} | {row['changed_task_count']} | "
            f"{row['public_score']} | {row['delta_vs_parent']} | {row['attribution_strength']} | "
            f"{row['decision']} | {row['keep_in_normal_bank']} | {row['keep_in_high_risk_bank']} |"
        )
    lines.extend(
        [
            "",
            "Broad mixes are bundle-level evidence only. High-risk wins remain outside the normal task bank.",
            "",
        ]
    )
    root("reports/TASK_ATTRIBUTION.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", default="")
    parser.add_argument("--all-completed", action="store_true")
    args = parser.parse_args()
    if not args.exp_id and not args.all_completed:
        raise SystemExit("use --exp-id or --all-completed")

    queue_path = root("experiments/submission_queue.csv")
    queue_fields, queue_rows = read_csv(queue_path)
    history_by_exp, best_score = history()
    selected = [
        row
        for row in queue_rows
        if (args.all_completed or row.get("exp_id") == args.exp_id)
        and truthy(row.get("submitted"))
    ]
    generated: list[dict] = []
    processed_exp_ids: set[str] = set()
    for row in selected:
        records = attribution_rows(
            row, history_by_exp=history_by_exp, best_score=best_score
        )
        if records:
            generated.extend(records)
            processed_exp_ids.add(row.get("exp_id", ""))
            row["task_attribution_status"] = "recorded"
            row["next_action"] = "review_attribution"

    output_path = root("task_bank/task_submission_delta.csv")
    _, existing = read_csv(output_path)
    if args.all_completed:
        merged = generated
    else:
        merged = [
            row for row in existing if row.get("exp_id") not in processed_exp_ids
        ] + generated
    write_csv(output_path, ATTRIBUTION_FIELDS, merged)
    write_csv(queue_path, queue_fields, queue_rows)
    update_best_by_task(generated)
    write_report(merged)
    print(f"attributed_experiments={len(processed_exp_ids)}")
    print(f"attribution_rows={len(generated)}")


if __name__ == "__main__":
    main()
