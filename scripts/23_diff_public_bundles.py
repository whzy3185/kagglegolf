from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.onnx_score import safe_profile_model
from neurogolf.paths import root


EXP_ID = "GOLF_20260607_002_public_6029_diff"
SOURCE_ID = "SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029"
PARENT_EXP_ID = "GOLF_20260607_001_public_6154_repro"
BOTTOM15 = {"task158", "task233", "task173", "task054", "task025", "task285", "task366", "task133", "task286", "task255", "task349", "task018", "task187", "task145", "task243"}


def find_6029_dir() -> Path:
    candidates = [
        root("data/external/public_bundles/jsrdcht_6029_submission_bundle/extracted"),
        root("external/public_notebooks/jsrdcht_6029"),
    ]
    for c in candidates:
        if c.exists() and len(list(c.glob("task*.onnx"))) >= 300:
            return c
    raise SystemExit("6029 bundle missing. Run scripts/12_reproduce_public_solution.py --dataset jsrdcht/neurogolf-6029-submission-bundle")


def classify(task_id: str, p6154: dict, p6029: dict) -> tuple[str, str, str]:
    if not p6029["onnx_load"] or p6029["banned_ops"]:
        return "reject", "high", "6029_load_or_rule_risk"
    delta_mem = p6029["memory_footprint_proxy"] - p6154["memory_footprint_proxy"]
    delta_cost = p6029["estimated_cost"] - p6154["estimated_cost"]
    delta_utility = p6029["estimated_utility"] - p6154["estimated_utility"]
    if delta_mem < -2048 and delta_cost <= 0:
        return "low_risk_memory_win", "low", "swap_6029"
    if task_id in BOTTOM15 and delta_mem < 0:
        return "aggressive_possible_win", "medium", "swap_6029_bottom15_memory_win"
    if delta_mem < -8192:
        return "aggressive_possible_win", "medium", "swap_6029_large_memory_win_even_cost_unknown"
    if delta_utility > 0.01:
        return "aggressive_possible_win", "medium", "swap_6029_utility_proxy_win"
    if task_id in BOTTOM15 and p6029["node_count"] != p6154["node_count"]:
        return "high_risk_boundary_or_unknown", "high", "probe_bottom15_structural_difference"
    return "hold", "medium", "keep_6154"


def main() -> None:
    base_dir = root("submissions/candidates/GOLF_20260607_001_public_6154_repro/onnx")
    source_dir = find_6029_dir()
    rows = []
    candidates = []
    for idx in range(1, 401):
        task_id = f"task{idx:03d}"
        p6154 = safe_profile_model(base_dir / f"{task_id}.onnx")
        p6029 = safe_profile_model(source_dir / f"{task_id}.onnx")
        rec, risk, action = classify(task_id, p6154, p6029)
        row = {
            "task_id": task_id,
            "source_6154_model": p6154["path"],
            "source_6029_model": p6029["path"],
            "onnx_load_6154": p6154["onnx_load"],
            "onnx_load_6029": p6029["onnx_load"],
            "file_size_6154": p6154["file_size"],
            "file_size_6029": p6029["file_size"],
            "node_count_6154": p6154["node_count"],
            "node_count_6029": p6029["node_count"],
            "initializer_count_6154": p6154["initializer_count"],
            "initializer_count_6029": p6029["initializer_count"],
            "parameter_bytes_6154": p6154["parameter_bytes"],
            "parameter_bytes_6029": p6029["parameter_bytes"],
            "memory_footprint_proxy_6154": p6154["memory_footprint_proxy"],
            "memory_footprint_proxy_6029": p6029["memory_footprint_proxy"],
            "estimated_cost_6154": p6154["estimated_cost"],
            "estimated_cost_6029": p6029["estimated_cost"],
            "estimated_utility_6154": f"{p6154['estimated_utility']:.6f}",
            "estimated_utility_6029": f"{p6029['estimated_utility']:.6f}",
            "delta_memory": p6029["memory_footprint_proxy"] - p6154["memory_footprint_proxy"],
            "delta_cost": p6029["estimated_cost"] - p6154["estimated_cost"],
            "delta_utility": f"{p6029['estimated_utility'] - p6154['estimated_utility']:.6f}",
            "banned_ops_6154": p6154["banned_ops"],
            "banned_ops_6029": p6029["banned_ops"],
            "risk": risk,
            "recommendation": rec,
            "recommended_action": action,
            "source_id": SOURCE_ID,
        }
        rows.append(row)
        if rec in {"low_risk_memory_win", "aggressive_possible_win", "high_risk_boundary_or_unknown"}:
            candidates.append(
                {
                    "task_id": task_id,
                    "candidate_model_path": p6029["path"],
                    "source_id": SOURCE_ID,
                    "source_exp_id": EXP_ID,
                    "method_family": rec,
                    "memory_footprint": p6029["memory_footprint_proxy"],
                    "parameter_count": p6029["parameter_count"],
                    "file_size": p6029["file_size"],
                    "cost_proxy": p6029["estimated_cost"],
                    "utility_proxy": f"{p6029['estimated_utility']:.6f}",
                    "local_valid": p6029["onnx_load"] and not p6029["banned_ops"],
                    "risk": risk,
                    "candidate_rank": "",
                    "recommended_action": action,
                    "base_memory": p6154["memory_footprint_proxy"],
                    "delta_memory": row["delta_memory"],
                    "delta_cost": row["delta_cost"],
                }
            )

    diff_path = root("task_bank/task_diff_6154_6029.csv")
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    with diff_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    for i, row in enumerate(sorted(candidates, key=lambda r: (r["risk"] != "low", int(r["delta_memory"])), reverse=False), start=1):
        row["candidate_rank"] = i
    overrides_path = root("task_bank/candidate_overrides_6029.csv")
    with overrides_path.open("w", newline="", encoding="utf-8") as f:
        fields = list(candidates[0]) if candidates else ["task_id"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)

    pool_path = root("task_bank/task_candidate_pool.csv")
    with pool_path.open("w", newline="", encoding="utf-8") as f:
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
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in candidates:
            writer.writerow({k: row.get(k, "") for k in fields})

    low = [c for c in candidates if c["method_family"] == "low_risk_memory_win"]
    aggr = [c for c in candidates if c["method_family"] == "aggressive_possible_win"]
    high = [c for c in candidates if c["method_family"] == "high_risk_boundary_or_unknown"]
    top_lines = []
    for label, subset in [("low_risk_memory_win", low[:10]), ("aggressive_possible_win", aggr[:10]), ("high_risk_boundary_or_unknown", high[:10])]:
        top_lines.append(f"## {label}")
        for c in subset:
            top_lines.append(f"- {c['task_id']}: delta_memory={c['delta_memory']} delta_cost={c['delta_cost']} risk={c['risk']}")
        top_lines.append("")
    report = "\n".join(
        [
            "# Diff 6154 vs 6029",
            "",
            f"exp_id: {EXP_ID}",
            f"parent_exp_id: {PARENT_EXP_ID}",
            f"source_id: {SOURCE_ID}",
            f"created_at: {datetime.now().isoformat(timespec='seconds')}",
            f"6154_dir: {base_dir}",
            f"6029_dir: {source_dir}",
            "",
            "Priority metric: memory_footprint_proxy. This proxy is shape-inference based and must be treated as a ranking signal, not official score.",
            "",
            f"candidate overrides: {len(candidates)}",
            f"low_risk_memory_win: {len(low)}",
            f"aggressive_possible_win: {len(aggr)}",
            f"high_risk_boundary_or_unknown: {len(high)}",
            "",
            *top_lines,
        ]
    )
    root("reports/DIFF_6154_VS_6029.md").write_text(report, encoding="utf-8")
    root("experiments", f"{EXP_ID}.md").write_text(
        report
        + "\n## Next action\n\nBuild and submit `GOLF_20260607_002_public_6029_aggressive_mix` from top candidate overrides.\n",
        encoding="utf-8",
    )
    print(diff_path)
    print(overrides_path)
    print(root("reports/DIFF_6154_VS_6029.md"))


if __name__ == "__main__":
    main()

