from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime

from _bootstrap import ROOT
from neurogolf.data_io import load_task, task_paths
from neurogolf.paths import root
from neurogolf.simple_exact import (
    ATTEMPT_FIELDS,
    BANK_FIELDS,
    build_simple_rule_onnx,
    detect_task_candidates,
    rel,
    row_from_candidate,
    task_candidate_path,
    task_count,
    validation_status,
    write_csv,
)


def ensure_data() -> None:
    data_dir = root("data/raw/neurogolf-2026")
    if task_count(data_dir) == 400:
        return
    result = subprocess.run(
        [sys.executable, "scripts/02_download_competition_data.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or task_count(data_dir) != 400:
        raise SystemExit(
            "official task data is missing and download failed:\n"
            + (result.stdout or "")
            + (result.stderr or "")
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-rules-per-task", type=int, default=3)
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    ensure_data()
    paths = task_paths(root("data/raw/neurogolf-2026"))
    if args.limit:
        paths = paths[: args.limit]

    bank_rows: list[dict] = []
    attempts: list[dict] = []
    rejected: list[dict] = []
    for path in paths:
        task_id = path.stem
        task = load_task(path)
        candidates = detect_task_candidates(task_id, task)
        eligible = 0
        best_rule = ""
        for candidate in candidates[: args.max_rules_per_task]:
            onnx_path = task_candidate_path(task_id, candidate.rule_name)
            if args.no_build:
                rejected.append(
                    {
                        "task_id": task_id,
                        "rule_name": candidate.rule_name,
                        "reason": "no_build_requested",
                    }
                )
                continue
            try:
                build_simple_rule_onnx(candidate.rule_name, candidate.params, onnx_path)
                ok, status = validation_status(task_id, onnx_path)
            except Exception as exc:
                rejected.append(
                    {
                        "task_id": task_id,
                        "rule_name": candidate.rule_name,
                        "reason": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            if not ok:
                rejected.append(
                    {
                        "task_id": task_id,
                        "rule_name": candidate.rule_name,
                        "reason": status,
                    }
                )
                continue
            bank_rows.append(row_from_candidate(candidate, onnx_path, status))
            eligible += 1
            if not best_rule:
                best_rule = candidate.rule_name

        attempts.append(
            {
                "task_id": task_id,
                "train_examples": len(task.get("train", [])),
                "detected_rule_count": len(candidates),
                "eligible_rule_count": eligible,
                "best_rule_name": best_rule,
                "status": "eligible" if eligible else ("detected_but_rejected" if candidates else "no_simple_rule"),
                "notes": "; ".join(
                    f"{item['rule_name']}={item['reason']}" for item in rejected if item["task_id"] == task_id
                )[:1000],
            }
        )

    bank_rows.sort(
        key=lambda row: (
            row["estimated_hidden_risk"] != "low",
            row["task_id"],
            row["rule_name"],
        )
    )
    attempts.sort(key=lambda row: row["task_id"])

    write_csv(root("task_bank/simple_exact_task_bank.csv"), BANK_FIELDS, bank_rows)
    write_csv(root("task_bank/simple_exact_scan_attempts.csv"), ATTEMPT_FIELDS, attempts)

    checked_at = datetime.now().isoformat(timespec="seconds")
    family_counts: dict[str, int] = {}
    for row in bank_rows:
        family_counts[row["rule_family"]] = family_counts.get(row["rule_family"], 0) + 1

    lines = [
        "# Simple Exact Task Bank",
        "",
        f"updated_at: {checked_at}",
        f"official_task_count: {task_count(root('data/raw/neurogolf-2026'))}",
        f"tasks_scanned: {len(paths)}",
        f"simple_exact_candidates_found: {len(bank_rows)}",
        f"tasks_with_eligible_candidate: {len({row['task_id'] for row in bank_rows})}",
        f"train_pass_requirement: 1.0",
        f"local_validation_requirement: pass",
        "",
        "## Family Counts",
        "",
        "| rule_family | eligible_rows |",
        "|---|---:|",
    ]
    for family, count in sorted(family_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {family} | {count} |")
    if not family_counts:
        lines.append("| none | 0 |")

    lines.extend(
        [
            "",
            "## Eligible Rows",
            "",
            "| task_id | rule | family | risk | validation | onnx |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in bank_rows[:80]:
        lines.append(
            f"| {row['task_id']} | {row['rule_name']} | {row['rule_family']} | "
            f"{row['estimated_hidden_risk']} | {row['local_validation_status']} | "
            f"{row['candidate_onnx_path']} |"
        )
    if len(bank_rows) > 80:
        lines.append(f"| ... | ... | ... | ... | ... | {len(bank_rows) - 80} more rows in CSV |")

    lines.extend(
        [
            "",
            "## Scan Coverage",
            "",
            "| status | task_count |",
            "|---|---:|",
        ]
    )
    status_counts: dict[str, int] = {}
    for row in attempts:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    for status, count in sorted(status_counts.items()):
        lines.append(f"| {status} | {count} |")

    lines.extend(
        [
            "",
            "## Rejected Train-Exact Candidates",
            "",
            "Rows below were not admitted to the bank because generation or local validation failed.",
            "",
        ]
    )
    for item in rejected[:80]:
        lines.append(f"- {item['task_id']} {item['rule_name']}: {item['reason']}")
    if len(rejected) > 80:
        lines.append(f"- ... {len(rejected) - 80} more rejected rows")
    lines.extend(
        [
            "",
            "## Data Source",
            "",
            "- Official JSON tasks are read from `data/raw/neurogolf-2026`.",
            "- Generated ONNX files live under `task_bank/tasks/*/simple_exact/` and are ignored by Git via the global `*.onnx` rule.",
            "- `submission (1).zip` is present locally and remains an untracked artifact for later source comparison; it is not copied into this bank.",
            "",
        ]
    )
    root("reports/SIMPLE_EXACT_TASK_BANK.md").write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "checked_at": checked_at,
        "tasks_scanned": len(paths),
        "bank_rows": len(bank_rows),
        "tasks_with_eligible_candidate": len({row["task_id"] for row in bank_rows}),
        "attempts_csv": rel(root("task_bank/simple_exact_scan_attempts.csv")),
        "bank_csv": rel(root("task_bank/simple_exact_task_bank.csv")),
    }
    root("data/manifests/simple_exact_task_bank.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(f"tasks_scanned={len(paths)}")
    print(f"simple_exact_candidates_found={len(bank_rows)}")
    print(f"tasks_with_eligible_candidate={len({row['task_id'] for row in bank_rows})}")


if __name__ == "__main__":
    main()
