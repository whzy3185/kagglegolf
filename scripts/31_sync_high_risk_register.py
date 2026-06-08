from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.paths import root


FIELDS = [
    "exp_id",
    "risk_reason",
    "source_id",
    "changed_tasks",
    "submission_id",
    "public_score",
    "delta_vs_best",
    "decision",
    "normal_bank_allowed",
    "notes",
]


def read_csv(path: Path) -> list[dict]:
    if not path.exists() or not path.stat().st_size:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def main() -> None:
    queue = read_csv(root("experiments/submission_queue.csv"))
    attribution = read_csv(root("task_bank/task_submission_delta.csv"))
    attribution_by_exp: dict[str, list[dict]] = {}
    for row in attribution:
        attribution_by_exp.setdefault(row.get("exp_id", ""), []).append(row)

    rows: list[dict] = []
    for item in queue:
        if str(item.get("risk", "")).lower() != "high":
            continue
        exp_id = item.get("exp_id", "")
        evidence = attribution_by_exp.get(exp_id, [])
        decisions = sorted({row.get("decision", "") for row in evidence if row.get("decision")})
        delta = item.get("score_delta_vs_best", "")
        row = {
            "exp_id": exp_id,
            "risk_reason": (
                "Public-source task substitution has uncertain hidden generalization "
                "and is isolated from the normal task bank."
            ),
            "source_id": item.get("source_id", ""),
            "changed_tasks": item.get("changed_tasks", ""),
            "submission_id": item.get("submission_id", ""),
            "public_score": item.get("public_score", ""),
            "delta_vs_best": delta,
            "decision": ",".join(decisions) or "pending_attribution",
            "normal_bank_allowed": "false",
            "notes": "High-risk evidence only; never use as a normal base without explicit promotion.",
        }
        rows.append(row)

        destination = root("submissions/high_risk", exp_id)
        destination.mkdir(parents=True, exist_ok=True)
        candidate_manifest = root("submissions/candidates", exp_id, "manifest.json")
        source_manifest = (
            json.loads(candidate_manifest.read_text(encoding="utf-8"))
            if candidate_manifest.exists()
            else {}
        )
        payload = {
            "exp_id": exp_id,
            "source_id": item.get("source_id", ""),
            "changed_tasks": [
                task
                for task in str(item.get("changed_tasks", "")).split(",")
                if task
            ],
            "package_sha256": source_manifest.get("package_sha256")
            or source_manifest.get("sha256", ""),
            "high_risk": True,
            "normal_bank_allowed": False,
            "submission_id": item.get("submission_id", ""),
            "public_score": item.get("public_score", ""),
            "decision": row["decision"],
        }
        (destination / "manifest.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        (destination / "score.md").write_text(
            "\n".join(
                [
                    f"# {exp_id}",
                    "",
                    f"submission_id: {item.get('submission_id', '')}",
                    f"public_score: {item.get('public_score', '')}",
                    f"delta_vs_best: {delta}",
                    f"decision: {row['decision']}",
                    "normal_bank_allowed: false",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    write_csv(root("task_bank/high_risk_task_bank.csv"), rows)
    lines = [
        "# High Risk Register",
        "",
        f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "High-risk candidates may be submitted, but cannot update the normal task bank or become a normal base without explicit promotion.",
        "",
        "| exp_id | source | changed tasks | submission | score | delta best | decision | normal bank |",
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['exp_id']} | {row['source_id']} | {row['changed_tasks']} | "
            f"{row['submission_id']} | {row['public_score']} | {row['delta_vs_best']} | "
            f"{row['decision']} | false |"
        )
    lines.append("")
    root("reports/HIGH_RISK_REGISTER.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(f"high_risk_candidates={len(rows)}")


if __name__ == "__main__":
    main()
