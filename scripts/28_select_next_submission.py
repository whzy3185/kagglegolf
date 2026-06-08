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
    "structural_scale_score",
    "large_structure_bonus",
    "small_tuning_penalty",
    "known_bad_family_penalty",
    "auto_selected_reason",
    "recent_negative_source_penalty",
    "same_family_negative_penalty",
    "source_diversity_bonus",
    "positive_probe_required_for_broad_mix",
    "attribution_value",
    "bottom_tail_or_memory_tail_bonus",
    "risk_penalty",
]

HARD_BLOCKED_STATUSES = {
    "failed_local_validation",
    "validation_fail",
    "evidence_gate_failed",
    "metadata_only",
    "notebook_missing",
    "missing_artifact",
    "empty_changed_tasks_rejected",
    "hard_gate_blocked",
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

STRUCTURAL_SCALE = {
    "full_bundle_replacement": 1.00,
    "solver_replacement": 0.90,
    "operator_family_replacement": 0.80,
    "large_subgraph_rewrite": 0.75,
    "top5_targeted_mix": 0.60,
    "single_task_probe": 0.50,
    "basic_cleanup": 0.15,
    "small_tuning": 0.05,
    "constant_tweak": 0.05,
    "metadata_only": 0.00,
}

LARGE_STRUCTURE_BONUS = {
    "full_bundle_replacement": 0.25,
    "solver_replacement": 0.20,
    "operator_family_replacement": 0.15,
    "large_subgraph_rewrite": 0.15,
}

SMALL_TUNING_PENALTY = {
    "small_tuning": 0.50,
    "constant_tweak": 0.45,
    "basic_cleanup": 0.35,
    "metadata_only": 1.00,
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


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists() or not path.stat().st_size:
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_queue(path: Path, fields: list[str], rows: list[dict]) -> None:
    fields = list(fields)
    for field in REQUIRED_QUEUE_FIELDS:
        if field not in fields:
            fields.append(field)
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
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
    state_path = root("reports/CURRENT_STATE.md")
    if not state_path.exists():
        return 0.0, ""
    state = state_path.read_text(encoding="utf-8")
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


def candidate_path(row: dict) -> Path:
    candidate = Path(str(row.get("candidate_path", "")))
    if candidate.exists():
        return candidate
    return root("submissions/candidates", row.get("exp_id", ""))


def artifact_exists(row: dict) -> bool:
    candidate = candidate_path(row)
    if (candidate / "submission.zip").exists():
        return True
    if (candidate / "notebook.ipynb").exists():
        return True
    if (candidate / "kaggle_kernel" / "notebook.ipynb").exists():
        return True
    return False


def ags_payload(exp_id: str) -> dict:
    path = root("data/manifests", f"aggressive_change_{exp_id}.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def structural_class(row: dict) -> str:
    tasks = changed_tasks(row)
    count = len(tasks)
    classification = str(row.get("aggressive_change_classification", "")).lower()
    if classification == "metadata_only":
        return "metadata_only"
    if count >= 300:
        return "full_bundle_replacement"
    payload = ags_payload(row.get("exp_id", ""))
    rewrite_classes = set((payload.get("rewrite_classes") or {}).keys())
    structural = payload.get("structural_delta_components") or {}
    op_delta = as_float(structural.get("op_family_delta"))
    topology = as_float(structural.get("topology_delta"))
    if "operator_family_rewrite" in rewrite_classes or op_delta >= 0.35:
        return "operator_family_replacement"
    if "topology_rewrite" in rewrite_classes or topology >= 0.30:
        return "large_subgraph_rewrite"
    if count == 1:
        return "single_task_probe"
    if 2 <= count <= 5:
        return "top5_targeted_mix"
    if count > 20:
        return "solver_replacement"
    if as_float(row.get("aggressive_change_score")) < 0.25:
        return "small_tuning"
    return "large_subgraph_rewrite" if count > 5 else "top5_targeted_mix"


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


def negative_delta(row: dict) -> bool:
    delta = as_float(row.get("delta_vs_parent"), 0.0)
    decision = str(row.get("decision", ""))
    return delta < -0.0001 or decision in {
        "rejected_for_current_base",
        "negative_or_mixed",
        "bundle_negative",
    }


def positive_probe(source_id: str, delta_rows: list[dict]) -> bool:
    for row in delta_rows:
        if row.get("source_id") != source_id:
            continue
        count = int(as_float(row.get("changed_task_count"), 999))
        if count > 5:
            continue
        if as_float(row.get("delta_vs_parent"), 0.0) > 0.0001:
            return True
    return False


def same_source_negative_penalty(row: dict, delta_rows: list[dict]) -> tuple[float, str]:
    source_id = row.get("source_id", "")
    negatives = [
        item
        for item in delta_rows
        if item.get("source_id") == source_id and negative_delta(item)
    ]
    if not negatives:
        return 0.0, ""
    worst = min(as_float(item.get("delta_vs_parent"), 0.0) for item in negatives)
    small_or_single_negatives = [
        item for item in negatives if int(as_float(item.get("changed_task_count"), 999)) <= 5
    ]
    if len(small_or_single_negatives) >= 2:
        penalty = 1.0
    else:
        penalty = min(1.0, 0.35 + min(0.35, abs(worst) / 50.0))
    examples = ", ".join(sorted({item.get("exp_id", "") for item in negatives})[:3])
    return penalty, f"recent negative source feedback from {examples}"


def same_family_penalty(row: dict, delta_rows: list[dict]) -> tuple[float, str]:
    tasks = changed_tasks(row)
    if not tasks & BOTTOM_TAIL:
        return 0.0, ""
    source_id = row.get("source_id", "")
    for item in delta_rows:
        if item.get("source_id") != source_id or not negative_delta(item):
            continue
        if str(item.get("task_id", "")) in BOTTOM_TAIL:
            return 1.0, "same source already has negative bottom-tail probe feedback"
    return 0.0, ""


def source_diversity_bonus(row: dict, queue_rows: list[dict], delta_rows: list[dict]) -> float:
    source_id = row.get("source_id", "")
    submitted_same_source = [
        item
        for item in queue_rows
        if item.get("source_id") == source_id and truthy(item.get("submitted"))
    ]
    if not submitted_same_source:
        return 1.0
    if any(item.get("source_id") == source_id and negative_delta(item) for item in delta_rows):
        return 0.0
    return 0.50


def expected_upside(row: dict, source: dict, delta_rows: list[dict], best_score: float) -> float:
    source_id = row.get("source_id", "")
    deltas = [
        as_float(item.get("delta_vs_parent"), 0.0)
        for item in delta_rows
        if item.get("source_id") == source_id
    ]
    if deltas and max(deltas) <= 0.0001 and min(deltas) >= -0.0001:
        return 0.45
    if deltas and max(deltas) > 0.0001:
        return 0.85
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
    return 0.45


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


def attribution_value(row: dict) -> float:
    count = len(changed_tasks(row))
    if count == 1:
        return 1.0
    if count <= 5:
        return 0.70
    if count > 20:
        return 0.20
    return 0.55


def bottom_tail_or_memory_tail_bonus(row: dict) -> float:
    tasks = changed_tasks(row)
    payload = ags_payload(row.get("exp_id", ""))
    memory_gain = as_float(
        (payload.get("memory_profile") or {}).get("expected_gain_ratio"),
        0.0,
    )
    if tasks & BOTTOM_TAIL and memory_gain > 0.05:
        return 1.0
    if tasks & BOTTOM_TAIL:
        return 0.75
    if memory_gain > 0.20:
        return 0.80
    if memory_gain > 0.05:
        return 0.45
    return 0.0


def risk_penalty(row: dict, high_risk_rows: list[dict]) -> float:
    base = {"low": 0.0, "medium": 0.35, "high": 0.70}.get(
        str(row.get("risk", "")).lower(), 0.35
    )
    if any(item.get("exp_id") == row.get("exp_id") for item in high_risk_rows):
        return max(base, 0.70)
    return base


def known_bad_penalty(row: dict, delta_rows: list[dict], known_bad_text: str) -> tuple[float, str]:
    source = row.get("source_id", "")
    tasks = changed_tasks(row)
    count = len(tasks)
    if source == "SRC_KAGGLE_NOTEBOOK_BEICICC_6645" and count > 5:
        return 0.70, "Beicicc broad structural-pass family scored 5948.07"
    if source == "SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX" and count > 20:
        return 0.70, "Jonathan broad structural-pass family scored 5595.78"
    if source == "SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029" and "task286" in tasks:
        return 0.30, "6029 task286 probe scored below current best"
    if str(row.get("status", "")).lower() == "failed_local_validation" and count > 20:
        return 0.70, "broad candidate originates from a failed local family"
    for item in delta_rows:
        if item.get("source_id") == source and item.get("task_id") in tasks and negative_delta(item):
            return 1.0, f"{item.get('task_id')} already rejected for current base"
    if source in known_bad_text and "known_bad_family" in known_bad_text and count > 20:
        return 0.70, "source appears in KNOWN_BAD_FAMILIES for broad-family failures"
    return 0.0, ""


def base_hard_filter(row: dict) -> list[str]:
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
    status = str(row.get("status", "")).lower()
    if status in HARD_BLOCKED_STATUSES:
        reasons.append(f"blocked_status:{row.get('status')}")
    if not changed_tasks(row):
        reasons.append("empty_changed_tasks")
    if not artifact_exists(row):
        reasons.append("missing_artifact")
    return reasons


def score_row(
    row: dict,
    *,
    sources: dict[str, dict],
    rows: list[dict],
    delta_rows: list[dict],
    high_risk_rows: list[dict],
    known_bad_text: str,
    best_score: float,
) -> dict:
    source = sources.get(row.get("leaderboard_source_id") or row.get("source_id"), {})
    structural = structural_class(row)
    large_bonus = LARGE_STRUCTURE_BONUS.get(structural, 0.0)
    if len(changed_tasks(row)) > 20 and positive_probe(row.get("source_id", ""), delta_rows):
        large_bonus = max(large_bonus, 0.10)
    structural_scale = min(1.0, STRUCTURAL_SCALE.get(structural, 0.35) + large_bonus)
    small_penalty = SMALL_TUNING_PENALTY.get(structural, 0.0)
    bad_penalty, bad_reason = known_bad_penalty(row, delta_rows, known_bad_text)
    negative_source_penalty, negative_source_reason = same_source_negative_penalty(row, delta_rows)
    same_family_penalty_value, same_family_reason = same_family_penalty(row, delta_rows)
    diversity_bonus = source_diversity_bonus(row, rows, delta_rows)
    broad_without_positive = (
        20 < len(changed_tasks(row)) < 300
        and not positive_probe(row.get("source_id", ""), delta_rows)
    )
    components = {
        "ags": as_float(row.get("aggressive_change_score")),
        "structural_scale_score": structural_scale,
        "source_priority_score": source_priority(source),
        "expected_lb_upside": expected_upside(row, source, delta_rows, best_score),
        "novelty_vs_submitted": novelty(row, rows),
        "attribution_value": attribution_value(row),
        "bottom_tail_or_memory_tail_bonus": bottom_tail_or_memory_tail_bonus(row),
        "known_bad_family_penalty": bad_penalty,
        "small_tuning_penalty": small_penalty,
        "recent_negative_source_penalty": negative_source_penalty,
        "same_family_negative_penalty": same_family_penalty_value,
        "source_diversity_bonus": diversity_bonus,
        "risk_penalty": risk_penalty(row, high_risk_rows),
    }
    total = (
        0.22 * components["ags"]
        + 0.20 * components["structural_scale_score"]
        + 0.18 * components["source_priority_score"]
        + 0.15 * components["expected_lb_upside"]
        + 0.10 * components["source_diversity_bonus"]
        + 0.10 * components["attribution_value"]
        + 0.05 * components["bottom_tail_or_memory_tail_bonus"]
        - 0.20 * components["recent_negative_source_penalty"]
        - 0.20 * components["same_family_negative_penalty"]
        - 0.15 * components["known_bad_family_penalty"]
        - 0.10 * components["risk_penalty"]
        - 0.15 * components["small_tuning_penalty"]
    )
    reason_parts = [
        f"class={structural}",
        f"AGS={components['ags']:.3f}",
        f"structural_scale={components['structural_scale_score']:.2f}",
        f"source={components['source_priority_score']:.2f}",
        f"upside={components['expected_lb_upside']:.2f}",
        f"novelty={components['novelty_vs_submitted']:.2f}",
        f"attribution={components['attribution_value']:.2f}",
        f"tail_bonus={components['bottom_tail_or_memory_tail_bonus']:.2f}",
        f"known_bad_penalty={components['known_bad_family_penalty']:.2f}",
        f"small_tuning_penalty={components['small_tuning_penalty']:.2f}",
        f"recent_negative_source_penalty={components['recent_negative_source_penalty']:.2f}",
        f"same_family_negative_penalty={components['same_family_negative_penalty']:.2f}",
        f"source_diversity_bonus={components['source_diversity_bonus']:.2f}",
        f"risk_penalty={components['risk_penalty']:.2f}",
    ]
    if bad_reason:
        reason_parts.append(f"known_bad={bad_reason}")
    if negative_source_reason:
        reason_parts.append(f"source_negative={negative_source_reason}")
    if same_family_reason:
        reason_parts.append(f"same_family_negative={same_family_reason}")
    if broad_without_positive:
        reason_parts.append("positive_probe_required_for_broad_mix=true")
    return {
        "exp_id": row.get("exp_id", ""),
        "selection_score": round(total, 6),
        "selection_reason": "; ".join(reason_parts),
        "risk": row.get("risk", ""),
        "source_id": row.get("source_id", ""),
        "changed_task_count": len(changed_tasks(row)),
        "lane": "high_risk" if str(row.get("risk", "")).lower() == "high" else "normal",
        "structural_class": structural,
        "large_structure_bonus": large_bonus,
        "positive_probe_required_for_broad_mix": broad_without_positive,
        "components": components,
        "package_sha256": package_sha(row),
        "soft_penalties": (
            ["positive_probe_required_for_broad_mix"] if broad_without_positive else []
        )
        + (["low_value_tuning"] if small_penalty >= 0.35 else []),
    }


def update_row_from_score(row: dict, item: dict, rank: int | None) -> None:
    row["selection_score"] = f"{item['selection_score']:.6f}"
    row["selected_rank"] = str(rank or "")
    row["selection_reason"] = item["selection_reason"]
    row["auto_selected_reason"] = item["selection_reason"]
    row["structural_scale_score"] = f"{item['components']['structural_scale_score']:.6f}"
    row["large_structure_bonus"] = f"{item['large_structure_bonus']:.6f}"
    row["small_tuning_penalty"] = f"{item['components']['small_tuning_penalty']:.6f}"
    row["known_bad_family_penalty"] = f"{item['components']['known_bad_family_penalty']:.6f}"
    row["recent_negative_source_penalty"] = f"{item['components']['recent_negative_source_penalty']:.6f}"
    row["same_family_negative_penalty"] = f"{item['components']['same_family_negative_penalty']:.6f}"
    row["source_diversity_bonus"] = f"{item['components']['source_diversity_bonus']:.6f}"
    row["positive_probe_required_for_broad_mix"] = str(item["positive_probe_required_for_broad_mix"]).lower()
    row["attribution_value"] = f"{item['components']['attribution_value']:.6f}"
    row["bottom_tail_or_memory_tail_bonus"] = f"{item['components']['bottom_tail_or_memory_tail_bonus']:.6f}"
    row["risk_penalty"] = f"{item['components']['risk_penalty']:.6f}"


def soft_penalty_labels(item: dict) -> list[str]:
    labels = list(item.get("soft_penalties") or [])
    components = item.get("components") or {}
    if as_float(components.get("recent_negative_source_penalty")) > 0:
        labels.append("recent_negative_source_penalty")
    if as_float(components.get("same_family_negative_penalty")) > 0:
        labels.append("same_family_negative_penalty")
    if as_float(components.get("known_bad_family_penalty")) > 0:
        labels.append("known_bad_family_penalty")
    if as_float(components.get("expected_lb_upside")) <= 0.25:
        labels.append("low_expected_lb_upside")
    if as_float(item.get("selection_score")) < 0.35:
        labels.append("low_selection_score")
    return sorted(set(labels))


def main() -> None:
    queue_path = root("experiments/submission_queue.csv")
    fields, rows = read_csv(queue_path)
    if not fields:
        fields = list(REQUIRED_QUEUE_FIELDS)
    sources = parse_evidence_registry(root("research/EVIDENCE_REGISTRY.md"))
    _, delta_rows = read_csv(root("task_bank/task_submission_delta.csv"))
    _, high_risk_rows = read_csv(root("task_bank/high_risk_task_bank.csv"))
    known_bad_path = root("reports/KNOWN_BAD_FAMILIES.md")
    known_bad_text = known_bad_path.read_text(encoding="utf-8") if known_bad_path.exists() else ""
    best_score, best_exp_id = current_best()
    blocked: list[dict] = []
    scored: list[dict] = []

    for row in rows:
        row["selected_rank"] = ""
        row["selection_score"] = row.get("selection_score", "")
        reasons = base_hard_filter(row)
        if reasons:
            blocked.append({"exp_id": row.get("exp_id", ""), "reasons": reasons})
            if not truthy(row.get("submitted")):
                row["selection_reason"] = "blocked: " + ", ".join(reasons)
            continue
        item = score_row(
            row,
            sources=sources,
            rows=rows,
            delta_rows=delta_rows,
            high_risk_rows=high_risk_rows,
            known_bad_text=known_bad_text,
            best_score=best_score,
        )
        scored.append(item)

    scored.sort(key=lambda item: (-item["selection_score"], item["exp_id"]))
    rank_by_exp = {item["exp_id"]: index for index, item in enumerate(scored, start=1)}
    score_by_exp = {item["exp_id"]: item for item in scored}
    for row in rows:
        item = score_by_exp.get(row.get("exp_id", ""))
        if item:
            update_row_from_score(row, item, rank_by_exp[item["exp_id"]])

    write_queue(queue_path, fields, rows)
    selected = scored[0] if scored else None
    payload = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "current_best_score": best_score,
        "current_best_exp_id": best_exp_id,
        "candidate_count": len(rows),
        "eligible_count": len(scored),
        "blocked_count": len(blocked),
        "selected_exp_id": selected["exp_id"] if selected else "",
        "selected": selected,
        "ranked_candidates": scored,
        "blocked_candidates": blocked,
        "policy": "selection_ordering_only_soft_penalties_do_not_block",
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
        f"eligible_count: {len(scored)}",
        f"blocked_count: {len(blocked)}",
        f"selected_candidate: {payload['selected_exp_id'] or 'none'}",
        f"selection_score: {selected['selection_score'] if selected else ''}",
        f"selection_reason: {selected['selection_reason'] if selected else 'No eligible candidate.'}",
        "",
        "policy: selection is ordering only, not a blocking gate",
        "soft_penalties: affect submit order only; hard blocks are local validation, evidence gate, AGS gate, missing artifact, empty changed_tasks, already submitted, or explicit validation/evidence/metadata failure.",
        "",
        "## Eligible Submit Order",
        "",
        "| order | exp_id | score | soft_penalties |",
        "|---:|---|---:|---|",
    ]
    for index, item in enumerate(scored, start=1):
        lines.append(
            f"| {index} | {item['exp_id']} | {item['selection_score']:.6f} | "
            f"{', '.join(soft_penalty_labels(item)) or 'none'} |"
        )
    if not scored:
        lines.append("| - | none | - | - |")
    lines.extend(
        [
            "",
            "## Top 10",
            "",
            "| rank | exp_id | score | class | risk | tasks | source |",
            "|---:|---|---:|---|---|---:|---|",
        ]
    )
    for index, item in enumerate(scored[:10], start=1):
        lines.append(
            f"| {index} | {item['exp_id']} | {item['selection_score']:.6f} | "
            f"{item['structural_class']} | {item['risk']} | {item['changed_task_count']} | {item['source_id']} |"
        )
    if not scored:
        lines.append("| - | none | - | - | - | - | - |")
    lines.extend(["", "## Blocked Candidates", ""])
    lines.extend(
        f"- {item['exp_id']}: {', '.join(item['reasons'])}" for item in blocked
    )
    lines.extend(
        [
            "",
            "## Negative Feedback Policy",
            "",
            "Same-source, same-family, known-bad, low-upside, and broad-without-positive-probe signals reduce rank only. They do not block candidates that pass hard gates.",
            "",
            "## Next Action",
            "",
            (
                "Submit all hard-gate eligible candidates through `scripts/19_submit_queue.py --submit-all-eligible --limit 999`."
                if selected
                else "Generate a validator-pass probe candidate, score it with AGS, then rerun selection."
            ),
            "",
        ]
    )
    root("reports/NEXT_SUBMISSION_SELECTION.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    eligibility_lines = [
        "# Submit Eligibility",
        "",
        f"checked_at: {payload['checked_at']}",
        "policy: hard gates decide eligibility; soft penalties only order submissions.",
        "",
        "| exp_id | eligible | hard_gate_status | soft_penalties | submit_order | reason |",
        "|---|---:|---|---|---:|---|",
    ]
    rank_lookup = {item["exp_id"]: index for index, item in enumerate(scored, start=1)}
    item_lookup = {item["exp_id"]: item for item in scored}
    blocked_lookup = {item["exp_id"]: item["reasons"] for item in blocked}
    for row in rows:
        exp_id = row.get("exp_id", "")
        if exp_id in item_lookup:
            item = item_lookup[exp_id]
            eligibility_lines.append(
                f"| {exp_id} | true | pass | {', '.join(soft_penalty_labels(item)) or 'none'} | "
                f"{rank_lookup[exp_id]} | eligible; soft penalties do not block |"
            )
        else:
            reasons = blocked_lookup.get(exp_id, base_hard_filter(row))
            status = ", ".join(reasons) if reasons else "not_scored"
            eligibility_lines.append(
                f"| {exp_id} | false | {status} | not_applicable |  | hard_gate_blocked |"
            )
    root("reports/SUBMIT_ELIGIBILITY.md").write_text(
        "\n".join(eligibility_lines) + "\n",
        encoding="utf-8",
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
    print(f"eligible={len(scored)}")
    print(f"selected={payload['selected_exp_id'] or 'none'}")


if __name__ == "__main__":
    main()
