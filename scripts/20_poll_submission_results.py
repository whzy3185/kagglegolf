from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.paths import root


REQUIRED_QUEUE_FIELDS = [
    "exp_id",
    "candidate_path",
    "risk",
    "direction_id",
    "leaderboard_source_id",
    "paper_source_id",
    "open_repo_source_id",
    "historical_competition_source_id",
    "source_id",
    "evidence_gate_status",
    "duplicate_hash",
    "aggressive_change_score",
    "aggressive_change_classification",
    "aggressive_change_gate_status",
    "changed_tasks",
    "local_valid",
    "notebook_ready",
    "submitted",
    "submission_id",
    "public_score",
    "status",
    "next_action",
    "selection_score",
    "selected_rank",
    "selection_reason",
    "score_delta_vs_best",
    "score_delta_vs_parent",
    "task_attribution_status",
]


def parse_score(value: object) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def read_parent_exp_id(row: dict) -> str:
    candidate = Path(row.get("candidate_path", ""))
    if not candidate.exists():
        candidate = root("submissions/candidates", row.get("exp_id", ""))
    manifest_path = candidate / "manifest.json"
    if not manifest_path.exists():
        return ""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    base = str(manifest.get("base", "")).replace("\\", "/").rstrip("/")
    return base.rsplit("/", 1)[-1] if base else ""


def complete_status(value: object) -> bool:
    return "complete" in str(value).lower()


def update_wait_report(exp_id: str, history_row: dict) -> None:
    path = root("reports", f"SUBMISSION_WAIT_{exp_id}.md")
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    status = str(history_row.get("status", ""))
    score = str(history_row.get("publicScore", ""))
    submission_id = str(history_row.get("ref", ""))
    outcome = "complete" if complete_status(status) and score else status or "pending"
    replacements = {
        "updated_at:": f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
        "outcome:": f"outcome: {outcome}",
        "submission_id:": f"submission_id: {submission_id}",
        "status:": f"status: {status}",
        "public_score:": f"public_score: {score}",
    }
    lines = text.splitlines()
    seen = set()
    for index, line in enumerate(lines):
        for prefix, replacement in replacements.items():
            if prefix in seen or not line.startswith(prefix):
                continue
            lines[index] = replacement
            seen.add(prefix)
            break
    event = (
        f"| {datetime.now().isoformat(timespec='seconds')} | {status} | "
        f"{score} | {submission_id} |"
    )
    if event not in lines:
        lines.append(event)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", default="")
    args = parser.parse_args()

    subprocess.run(
        [sys.executable, "scripts/09_query_submission_history.py"],
        cwd=str(ROOT),
        check=False,
    )
    history_path = root("data/manifests/kaggle_submission_history.json")
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else {}
    rows_by_exp = {}
    for row in history.get("rows", []):
        desc = row.get("description", "")
        exp_id = desc.split("|", 1)[0].strip()
        if exp_id:
            rows_by_exp[exp_id] = row
    best_public = parse_score(history.get("best_public", {}).get("publicScore"))
    scores_by_exp = {
        exp_id: parse_score(item.get("publicScore"))
        for exp_id, item in rows_by_exp.items()
    }

    queue_path = root("experiments/submission_queue.csv")
    if not queue_path.exists():
        print("no submission queue")
        return
    with queue_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        queue = list(reader)
        fields = list(reader.fieldnames or [])
    for field in REQUIRED_QUEUE_FIELDS:
        if field not in fields:
            fields.append(field)
    for row in queue:
        exp_id = row.get("exp_id", "")
        if args.exp_id and exp_id != args.exp_id:
            continue
        hist = rows_by_exp.get(exp_id)
        if hist:
            update_wait_report(exp_id, hist)
            row["submitted"] = "true"
            row["submission_id"] = hist.get("ref", "")
            row["public_score"] = hist.get("publicScore", "")
            row["status"] = hist.get("status", "")
            score = parse_score(hist.get("publicScore"))
            parent_exp_id = read_parent_exp_id(row)
            parent_score = scores_by_exp.get(parent_exp_id)
            if parent_score is None and parent_exp_id == history.get(
                "best_public", {}
            ).get("exp_id"):
                parent_score = best_public
            row["score_delta_vs_best"] = (
                f"{score - best_public:.6f}"
                if score is not None and best_public is not None
                else ""
            )
            row["score_delta_vs_parent"] = (
                f"{score - parent_score:.6f}"
                if score is not None and parent_score is not None
                else ""
            )
            if complete_status(hist.get("status")) and score is not None:
                row["next_action"] = "record_task_attribution"
                if row.get("task_attribution_status") not in {"recorded", "complete"}:
                    row["task_attribution_status"] = "ready"
            else:
                row["next_action"] = "poll_submission_results"
                row["task_attribution_status"] = row.get(
                    "task_attribution_status", ""
                ) or "pending_score"
    with queue_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row.get(k, "") for k in fields} for row in queue)
    print(queue_path)


if __name__ == "__main__":
    main()
