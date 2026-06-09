from __future__ import annotations

import argparse
import csv
import hashlib
import re
import subprocess
import sys
from pathlib import Path

from _bootstrap import ROOT


DEFAULT_SOURCE_ID = "SRC_HF_ROGERMT_6273_SUBMISSION"
DEFAULT_DIRECTION_ID = "DIR_20260608_003_memory_first_onnx_surgery"
DEFAULT_PAPER_ID = "SRC_ARC_PRIZE_2024_REPORT"
DEFAULT_OPEN_REPO_ID = "SRC_ARC_DSL_GITHUB"
DEFAULT_HISTORICAL_ID = "SRC_GOOGLE_CODE_GOLF_2025"


def root(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


def read_csv(path: Path) -> list[dict]:
    if not path.exists() or not path.stat().st_size:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root(path)


def current_best_candidate() -> str:
    text = root("reports/CURRENT_STATE.md").read_text(encoding="utf-8")
    match = re.search(
        r"^Current best candidate artifact path:\s*(submissions/candidates/[^/\\]+)",
        text,
        re.MULTILINE,
    )
    if not match:
        raise SystemExit("Cannot resolve current best candidate from reports/CURRENT_STATE.md")
    return match.group(1)


def current_best_score() -> float:
    text = root("reports/SCORECARD.md").read_text(encoding="utf-8")
    match = re.search(r"^Current best public score:\s*([0-9.]+)", text, re.MULTILINE)
    return float(match.group(1)) if match else 0.0


def selected_rows(args: argparse.Namespace, base_dir: Path) -> list[dict]:
    include = {item.strip() for item in args.include_tasks.split(",") if item.strip()}
    exclude = {item.strip() for item in args.exclude_tasks.split(",") if item.strip()}
    rows = []
    for row in read_csv(root("task_bank/best_by_task.csv")):
        task_id = row.get("task_id", "")
        if include and task_id not in include:
            continue
        if task_id in exclude:
            continue
        if row.get("source_id") != args.source_id:
            continue
        if row.get("status") not in {"confirmed_lb_win", "suspected_win"}:
            continue
        try:
            delta = float(row.get("lb_delta_if_known") or 0)
        except ValueError:
            delta = 0.0
        if delta < args.min_delta:
            continue
        model_path = resolve(row.get("best_model_path", ""))
        if not model_path.exists():
            continue
        base_model = base_dir / f"{task_id}.onnx"
        if base_model.exists() and sha256(base_model) == sha256(model_path):
            continue
        rows.append(
            {
                "task_id": task_id,
                "candidate_model_path": str(model_path),
                "source_id": args.source_id,
                "source_exp_id": row.get("last_changed_exp_id", ""),
                "method_family": "score_delta_stack",
                "memory_footprint": "",
                "parameter_count": "",
                "file_size": model_path.stat().st_size,
                "cost_proxy": row.get("local_cost", ""),
                "utility_proxy": f"{delta:.6f}",
                "local_valid": "true",
                "risk": args.risk,
                "candidate_rank": "",
                "recommended_action": "stack_probe",
                "delta_basis": f"{delta:.6f}",
            }
        )
    rows.sort(key=lambda item: float(item["delta_basis"]), reverse=True)
    for idx, row in enumerate(rows[: args.top_k], start=1):
        row["candidate_rank"] = str(idx)
    return rows[: args.top_k]


def build_candidate(args: argparse.Namespace, override_csv: Path) -> None:
    cmd = [
        sys.executable,
        str(root("scripts/13_single_task_override.py")),
        "--exp-id",
        args.exp_id,
        "--base",
        args.base,
        "--override-csv",
        str(override_csv),
        "--source-id",
        args.source_id,
        "--direction-id",
        args.direction_id,
        "--leaderboard-source-id",
        args.source_id,
        "--paper-source-id",
        args.paper_source_id,
        "--open-repo-source-id",
        args.open_repo_source_id,
        "--historical-competition-source-id",
        args.historical_source_id,
        "--risk",
        args.risk,
        "--validate",
        "--pack",
        "--build-notebook",
        "--record",
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", required=True)
    parser.add_argument("--base", default="")
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--direction-id", default=DEFAULT_DIRECTION_ID)
    parser.add_argument("--paper-source-id", default=DEFAULT_PAPER_ID)
    parser.add_argument("--open-repo-source-id", default=DEFAULT_OPEN_REPO_ID)
    parser.add_argument("--historical-source-id", default=DEFAULT_HISTORICAL_ID)
    parser.add_argument("--risk", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--min-delta", type=float, default=0.01)
    parser.add_argument("--include-tasks", default="")
    parser.add_argument("--exclude-tasks", default="")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    if not args.base:
        args.base = current_best_candidate()
    base_dir = resolve(args.base) / "onnx"
    rows = selected_rows(args, base_dir)
    if not rows:
        raise SystemExit("No positive delta rows available for stack candidate")

    override_csv = root("task_bank", f"score_delta_stack_{args.exp_id}.csv")
    fields = [
        "task_id",
        "candidate_model_path",
        "source_id",
        "source_exp_id",
        "method_family",
        "memory_footprint",
        "parameter_count",
        "file_size",
        "cost_proxy",
        "utility_proxy",
        "local_valid",
        "risk",
        "candidate_rank",
        "recommended_action",
        "delta_basis",
    ]
    write_csv(override_csv, fields, rows)

    report = root("reports", f"SCORE_DELTA_STACK_{args.exp_id}.md")
    lines = [
        f"# Score Delta Stack: {args.exp_id}",
        "",
        f"base: {args.base}",
        f"current_best_before_build: {current_best_score():.2f}",
        f"source_id: {args.source_id}",
        f"override_csv: {override_csv}",
        "",
        "## Selected Tasks",
        "",
        "| rank | task_id | delta_basis | source_exp_id | model |",
        "|---:|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['candidate_rank']} | {row['task_id']} | {row['delta_basis']} | "
            f"{row['source_exp_id']} | {row['candidate_model_path']} |"
        )
    lines.extend(
        [
            "",
            "## Architecture Note",
            "",
            "This candidate is generated by score-delta stacking: only task-level models with positive public-LB attribution are selected, already-present hashes in the base bundle are skipped, and the resulting bundle tests whether independently positive task substitutions compose.",
            "",
        ]
    )
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"override_csv={override_csv}")
    print("tasks=" + ",".join(row["task_id"] for row in rows))
    if not args.no_build:
        build_candidate(args, override_csv)


if __name__ == "__main__":
    main()
