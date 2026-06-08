from __future__ import annotations

import csv
import json
import math
import re
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

BLOCKED_STATUSES = {
    "failed_local_validation",
    "validation_fail",
    "evidence_gate_failed",
    "aggressive_change_gate_failed",
    "duplicate_package_rejected",
    "metadata_only",
    "blocked",
}

BOTTOM_TAIL = {
    "task158",
    "task233",
    "task173",
    "task054",
    "task025",
    "task285",
    "task366",
    "task133",
    "task286",
    "task255",
    "task349",
    "task018",
    "task187",
    "task145",
    "task243",
}


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def as_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def changed_tasks(row: dict) -> set[str]:
    return {
        item.strip()
        for item in str(row.get("changed_tasks", "")).split(",")
        if item.strip()
    }


def read_queue(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists() or not path.stat().st_size:
        return list(REQUIRED_QUEUE_FIELDS), []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    fields.extend(field for field in REQUIRED_QUEUE_FIELDS if field not in fields)
    return fields, rows


def write_queue(path: Path, fields: list[str], rows: list[dict]) -> None:
    for row in rows:
        fields.extend(field for field in row if field not in fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def parse_evidence_registry(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    headers = list(re.finditer(r"(?m)^##\s+(SRC_\S+)\s*$", text))
    sources: dict[str, dict] = {}
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[header.start() : end]

        def field(name: str) -> str:
            match = re.search(rf"(?m)^{re.escape(name)}:\s*(.*?)\s*$", block)
            return match.group(1).strip() if match else ""

        sources[header.group(1)] = {
            "source_type": field("source_type"),
            "claimed_score": as_float(field("claimed_score"), -1.0),
            "priority": field("priority"),
            "title": field("title"),
        }
    return sources


def current_best() -> tuple[float, str]:
    history = root("data/manifests/kaggle_submission_history.json")
    if history.exists():
        payload = json.loads(history.read_text(encoding="utf-8"))
        best = payload.get("best_public") or {}
        return as_float(best.get("publicScore")), str(best.get("exp_id", ""))
    state = root("reports/CURRENT_STATE.md").read_text(encoding="utf-8")
    score = re.search(r"(?m)^Current best LB:\s*([0-9.]+)", state)
    return (as_float(score.group(1)) if score else 0.0, "")


def package_sha(row: dict) -> str:
    candidate = Path(str(row.get("candidate_path", "")))
    if not candidate.exists():
        candidate = root("submissions/candidates", row.get("exp_id", ""))
    manifest = candidate / "manifest.json"
    if not manifest.exists():
        return ""
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    return str(payload.get("package_sha256") or payload.get("sha256") or "")


def hard_filter(row: dict) -> list[str]:
    reasons: list[str] = []
    if truthy(row.get("submitted")):
        reasons.append("already_submitted")
    if not truthy(row.get("local_valid")):
        reasons.append("local_validation_not_passed")
    if not truthy(row.get("notebook_ready")):
        reasons.append("notebook_not_ready")
    if str(row.get("evidence_gate_status", "")).lower() != "pass":
        reasons.append("evidence_gate_not_passed")
    if str(row.get("aggressive_change_gate_status", "")).lower() != "pass":
        reasons.append("aggressive_change_gate_not_passed")
    if truthy(row.get("duplicate_hash")):
        reasons.append("duplicate_hash")
    if str(row.get("status", "")).lower() in BLOCKED_STATUSES:
        reasons.append(f"blocked_status:{row.get('status')}")
    if not changed_tasks(row):
        reasons.append("empty_changed_tasks")
    return reasons


def source_priority(source: dict) -> float:
    priority = source.get("priority", "")
    source_type = source.get("source_type", "")
    if priority == "P0" and source_type in {"notebook", "dataset", "leaderboard"}:
        return 1.0
    if priority == "P0" and source_type == "discussion":
        return 0.75
    if priority == "P1" and source_type in {"notebook", "dataset", "discussion"}:
        return 0.65
    if source_type in {"github", "paper", "technical_report"}:
        return 0.55
    if priority in {"P2", "P3"}:
        return 0.30
    return 0.10


def source_results(rows: list[dict], source_id: str, best_score: float) -> list[float]:
    scores = [
        as_float(row.get("public_score"), -1.0)
        for row in rows
        if row.get("source_id") == source_id and truthy(row.get("submitted"))
    ]
    return [score - best_score for score in scores if score >= 0]


def expected_upside(
    row: dict, source: dict, all_rows: list[dict], best_score: float
) -> float:
    deltas = source_results(all_rows, row.get("source_id", ""), best_score)
    if deltas and max(deltas) < -0.001:
        return 0.10
    claimed = as_float(source.get("claimed_score"), -1.0)
    tasks = changed_tasks(row)
    if claimed > best_score:
        return 1.0
    if claimed >= best_score - 150:
        return 0.70
    if len(tasks) == 1 and tasks & BOTTOM_TAIL:
        return 0.65
    if len(tasks) > 20 and claimed >= 0 and claimed < best_score:
        return 0.25
    return 0.45 if deltas and max(deltas) >= -0.001 else 0.35


def novelty(row: dict, rows: list[dict]) -> float:
    current_tasks = changed_tasks(row)
    source_id = row.get("source_id", "")
    submitted = [item for item in rows if truthy(item.get("submitted"))]
    if not any(item.get("source_id") == source_id for item in submitted):
        return 1.0
    same_source = [item for item in submitted if item.get("source_id") == source_id]
    overlaps = []
    for item in same_source:
        other = changed_tasks(item)
        union = current_tasks | other
        overlaps.append(len(current_tasks & other) / len(union) if union else 1.0)
    overlap = max(overlaps, default=0.0)
    if overlap >= 0.90:
        return 0.0
    if overlap >= 0.50:
        return 0.25
    return 0.60


def task_focus(row: dict, source: dict, best_score: float) -> float:
    tasks = changed_tasks(row)
    count = len(tasks)
    if count == 1 and tasks & BOTTOM_TAIL:
        return 1.0
    if count <= 5:
        return 0.80
    if count <= 15:
        return 0.60
    if count > 50:
        claimed = as_float(source.get("claimed_score"), -1.0)
        return 0.70 if claimed > best_score else 0.25
    return 0.45


def feedback_value(row: dict) -> float:
    count = len(changed_tasks(row))
    if count == 1:
        return 1.0
    if count <= 5:
        return 0.70
    if count > 20:
        return 0.40
    return 0.55


def risk_penalty(row: dict) -> float:
    return {"low": 0.0, "medium": 0.10, "high": 0.20}.get(
        str(row.get("risk", "")).lower(), 0.10
    )


def known_bad_penalty(row: dict) -> tuple[float, str]:
    source = row.get("source_id", "")
    tasks = changed_tasks(row)
    count = len(tasks)
    if source == "SRC_KAGGLE_NOTEBOOK_BEICICC_6645" and count > 20:
        return 0.50, "Beicicc broad structural-pass family scored 5948.07"
    if source == "SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029" and "task286" in tasks:
        return 0.15, "6029 task286 probe scored below current best"
    if str(row.get("status", "")).lower() == "failed_local_validation" and count > 20:
        return 0.70, "broad candidate originates from a failed local family"
    if source == "SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX" and count > 20:
        return 0.50, "Jonathan broad structural-pass family scored 5595.78"
    return 0.0, ""


def score_row(
    row: dict, *, sources: dict[str, dict], rows: list[dict], best_score: float
) -> dict:
    source = sources.get(row.get("leaderboard_source_id") or row.get("source_id"), {})
    components = {
        "ags": as_float(row.get("aggressive_change_score")),
        "source_priority_score": source_priority(source),
        "expected_lb_upside": expected_upside(row, source, rows, best_score),
        "novelty_vs_submitted": novelty(row, rows),
        "task_focus_score": task_focus(row, source, best_score),
        "feedback_value": feedback_value(row),
        "risk_penalty": risk_penalty(row),
    }
    bad_penalty, bad_reason = known_bad_penalty(row)
    components["known_bad_family_penalty"] = bad_penalty
    total = (
        0.30 * components["ags"]
        + 0.20 * components["source_priority_score"]
        + 0.15 * components["expected_lb_upside"]
        + 0.15 * components["novelty_vs_submitted"]
        + 0.10 * components["task_focus_score"]
        + 0.10 * components["feedback_value"]
        - 0.10 * components["risk_penalty"]
        - 0.15 * components["known_bad_family_penalty"]
    )
    reason = (
        f"AGS={components['ags']:.3f}; source={components['source_priority_score']:.2f}; "
        f"upside={components['expected_lb_upside']:.2f}; novelty={components['novelty_vs_submitted']:.2f}; "
        f"focus={components['task_focus_score']:.2f}; feedback={components['feedback_value']:.2f}; "
        f"risk_penalty={components['risk_penalty']:.2f}"
    )
    if bad_reason:
        reason += f"; known_bad={bad_reason}"
    return {
        "exp_id": row.get("exp_id", ""),
        "selection_score": round(total, 6),
        "selection_reason": reason,
        "risk": row.get("risk", ""),
        "source_id": row.get("source_id", ""),
        "changed_task_count": len(changed_tasks(row)),
        "lane": "high_risk" if str(row.get("risk", "")).lower() == "high" else "normal",
        "components": components,
        "package_sha256": package_sha(row),
    }


def main() -> None:
    queue_path = root("experiments/submission_queue.csv")
    fields, rows = read_queue(queue_path)
    sources = parse_evidence_registry(root("research/EVIDENCE_REGISTRY.md"))
    best_score, best_exp_id = current_best()
    blocked: list[dict] = []
    ranked: list[dict] = []

    for row in rows:
        reasons = hard_filter(row)
        if reasons:
            blocked.append({"exp_id": row.get("exp_id", ""), "reasons": reasons})
            row["selected_rank"] = ""
            if not truthy(row.get("submitted")):
                row["selection_reason"] = "blocked: " + ", ".join(reasons)
            continue
        ranked.append(
            score_row(row, sources=sources, rows=rows, best_score=best_score)
        )

    ranked.sort(key=lambda item: (-item["selection_score"], item["exp_id"]))
    rank_by_exp = {item["exp_id"]: index for index, item in enumerate(ranked, start=1)}
    score_by_exp = {item["exp_id"]: item for item in ranked}
    for row in rows:
        item = score_by_exp.get(row.get("exp_id", ""))
        if item:
            row["selection_score"] = f"{item['selection_score']:.6f}"
            row["selected_rank"] = str(rank_by_exp[item["exp_id"]])
            row["selection_reason"] = item["selection_reason"]

    write_queue(queue_path, fields, rows)
    selected = ranked[0] if ranked else None
    payload = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "current_best_score": best_score,
        "current_best_exp_id": best_exp_id,
        "candidate_count": len(rows),
        "eligible_count": len(ranked),
        "blocked_count": len(blocked),
        "selected_exp_id": selected["exp_id"] if selected else "",
        "selected": selected,
        "ranked_candidates": ranked,
        "blocked_candidates": blocked,
    }
    manifest = root("data/manifests/next_submission_selection.json")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Next Submission Selection",
        "",
        f"checked_at: {payload['checked_at']}",
        f"current_best: {best_score:.2f} ({best_exp_id or 'unknown'})",
        f"candidate_count: {len(rows)}",
        f"eligible_count: {len(ranked)}",
        f"blocked_count: {len(blocked)}",
        f"selected_candidate: {payload['selected_exp_id'] or 'none'}",
        f"selection_score: {selected['selection_score'] if selected else ''}",
        f"selection_reason: {selected['selection_reason'] if selected else 'No eligible candidate.'}",
        "",
        "## Top 10",
        "",
        "| rank | exp_id | score | risk | tasks | source |",
        "|---:|---|---:|---|---:|---|",
    ]
    for index, item in enumerate(ranked[:10], start=1):
        lines.append(
            f"| {index} | {item['exp_id']} | {item['selection_score']:.6f} | "
            f"{item['risk']} | {item['changed_task_count']} | {item['source_id']} |"
        )
    if not ranked:
        lines.append("| - | none | - | - | - | - |")
    lines.extend(["", "## Blocked Candidates", ""])
    lines.extend(
        f"- {item['exp_id']}: {', '.join(item['reasons'])}" for item in blocked
    )
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            (
                f"Submit `{payload['selected_exp_id']}` through `scripts/19_submit_queue.py --auto-select --limit 1`."
                if selected
                else "Generate a validator-pass probe candidate, score it with AGS, then rerun selection."
            ),
            "",
        ]
    )
    root("reports/NEXT_SUBMISSION_SELECTION.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    state_path = root("reports/CURRENT_STATE.md")
    if state_path.exists():
        state = state_path.read_text(encoding="utf-8")
        next_exp = payload["selected_exp_id"]
        state = re.sub(
            r"(?m)^Current candidate in queue:.*$",
            f"Current candidate in queue: {next_exp}",
            state,
        )
        state = re.sub(
            r"(?m)^Next candidate:.*$",
            f"Next candidate: {next_exp or 'generate_new_probe'}",
            state,
        )
        state = re.sub(
            r"(?m)^Last updated:.*$",
            f"Last updated: {payload['checked_at']}",
            state,
        )
        state_path.write_text(state, encoding="utf-8")
    print(f"eligible={len(ranked)}")
    print(f"selected={payload['selected_exp_id'] or 'none'}")


if __name__ == "__main__":
    main()
