from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.onnx_build import (
    build_dynamic_first_hsplit_network,
    build_fixed_crop_network,
    build_fixed_mirror_concat_network,
    build_fixed_mirror_tile_network,
    build_most_color_canvas_network,
)
from neurogolf.validation import validate_onnx_file

sys.path.insert(0, str(ROOT / "scripts" / "neurogolf"))
from _task_table import load_official_utils, score_one_task  # type: ignore  # noqa: E402


CURRENT_BEST = "GOLF_20260609_061_arc_dsl_task325_component_count_diagonal"
BEST_DIR = ROOT / "submissions" / "candidates" / CURRENT_BEST / "onnx"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fnum(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return default


def build_specs() -> list[dict]:
    return [
        {
            "task_id": "task067",
            "arc_id": "2dee498d",
            "primitive": "first_hsplit_3",
            "builder": lambda p: build_dynamic_first_hsplit_network(p, parts=3),
        },
        {
            "task_id": "task083",
            "arc_id": "f25ffba3_like_tile",
            "primitive": "fixed_mirror_tile_3x4",
            "builder": lambda p: build_fixed_mirror_tile_network(p, height=3, width=4),
        },
        {
            "task_id": "task142",
            "arc_id": "mirror_tile_3x3",
            "primitive": "fixed_mirror_tile_3x3",
            "builder": lambda p: build_fixed_mirror_tile_network(p, height=3, width=3),
        },
        {
            "task_id": "task152",
            "arc_id": "mirror_tile_3x3",
            "primitive": "fixed_mirror_tile_3x3",
            "builder": lambda p: build_fixed_mirror_tile_network(p, height=3, width=3),
        },
        {
            "task_id": "task116",
            "arc_id": "8be77c9e",
            "primitive": "fixed_vconcat_vmirror_3x4",
            "builder": lambda p: build_fixed_mirror_concat_network(
                p, height=3, width=4, mode="vconcat_vmirror"
            ),
        },
        {
            "task_id": "task164",
            "arc_id": "6d0aefbc",
            "primitive": "fixed_hconcat_hmirror_3x3",
            "builder": lambda p: build_fixed_mirror_concat_network(
                p, height=3, width=3, mode="hconcat_hmirror"
            ),
        },
        {
            "task_id": "task172",
            "arc_id": "8be77c9e",
            "primitive": "fixed_vconcat_vmirror_3x3",
            "builder": lambda p: build_fixed_mirror_concat_network(
                p, height=3, width=3, mode="vconcat_vmirror"
            ),
        },
        {
            "task_id": "task210",
            "arc_id": "8be77c9e",
            "primitive": "fixed_vconcat_vmirror_3x3",
            "builder": lambda p: build_fixed_mirror_concat_network(
                p, height=3, width=3, mode="vconcat_vmirror"
            ),
        },
        {
            "task_id": "task311",
            "arc_id": "6d0aefbc",
            "primitive": "fixed_hconcat_hmirror_3x3",
            "builder": lambda p: build_fixed_mirror_concat_network(
                p, height=3, width=3, mode="hconcat_hmirror"
            ),
        },
        {
            "task_id": "task129",
            "arc_id": "5582e5ca",
            "primitive": "most_color_canvas_3x3",
            "builder": lambda p: build_most_color_canvas_network(p, height=3, width=3),
        },
        {
            "task_id": "task135",
            "arc_id": "5bd6f4ac",
            "primitive": "fixed_crop_r0_c6_3x3",
            "builder": lambda p: build_fixed_crop_network(
                p, row_start=0, col_start=6, height=3, width=3
            ),
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-gain", type=float, default=0.05)
    args = parser.parse_args()

    utils, utils_status = load_official_utils()
    rows: list[dict] = []
    for spec in build_specs():
        task_id = spec["task_id"]
        task_num = int(task_id[-3:])
        out_path = ROOT / "task_bank" / "tasks" / task_id / f"{task_id}.onnx"
        status = "rejected"
        error = ""
        try:
            spec["builder"](out_path)
            validation = validate_onnx_file(
                out_path,
                ROOT / "data" / "raw" / "neurogolf-2026",
                smoke_examples_per_split=10_000,
            )
            candidate = score_one_task(
                out_path,
                task_num,
                f"prefilter_{task_id}",
                utils,
                utils_status,
            )
            base = score_one_task(
                BEST_DIR / f"{task_id}.onnx",
                task_num,
                f"base_{task_id}",
                utils,
                utils_status,
            )
            candidate_score = fnum(candidate.get("current_score"))
            base_score = fnum(base.get("current_score"))
            gain = candidate_score - base_score
            if validation.ok and candidate.get("correctness") == "pass" and gain > args.min_gain:
                status = "accepted"
            rows.append(
                {
                    "task_id": task_id,
                    "arc_id": spec["arc_id"],
                    "primitive": spec["primitive"],
                    "candidate_model_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                    "candidate_score": f"{candidate_score:.6f}",
                    "base_score": f"{base_score:.6f}",
                    "delta_score": f"{gain:.6f}",
                    "candidate_total_cost": candidate.get("total_cost", ""),
                    "base_total_cost": base.get("total_cost", ""),
                    "candidate_correctness": candidate.get("correctness", ""),
                    "validation_ok": str(validation.ok).lower(),
                    "examples_checked": validation.examples_checked,
                    "examples_failed": validation.examples_failed,
                    "status": status,
                    "error": error,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "task_id": task_id,
                    "arc_id": spec["arc_id"],
                    "primitive": spec["primitive"],
                    "candidate_model_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                    "candidate_score": "",
                    "base_score": "",
                    "delta_score": "",
                    "candidate_total_cost": "",
                    "base_total_cost": "",
                    "candidate_correctness": "error",
                    "validation_ok": "false",
                    "examples_checked": "",
                    "examples_failed": "",
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    out_csv = ROOT / "task_bank" / "arc_dsl_compact_prefilter.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id",
        "arc_id",
        "primitive",
        "candidate_model_path",
        "candidate_score",
        "base_score",
        "delta_score",
        "candidate_total_cost",
        "base_total_cost",
        "candidate_correctness",
        "validation_ok",
        "examples_checked",
        "examples_failed",
        "status",
        "error",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)

    accepted = [r for r in rows if r["status"] == "accepted"]
    report = ROOT / "reports" / "ARC_DSL_COMPACT_PREFILTER.md"
    lines = [
        "# ARC-DSL Compact Prefilter",
        "",
        f"updated_at: {iso_now()}",
        f"current_best: {CURRENT_BEST}",
        f"min_gain: {args.min_gain}",
        f"accepted: {len(accepted)}",
        "",
        "| task | primitive | base_score | candidate_score | delta | base_cost | candidate_cost | status |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in sorted(rows, key=lambda r: fnum(r.get("delta_score"), -999), reverse=True):
        lines.append(
            f"| {row['task_id']} | {row['primitive']} | {row['base_score']} | "
            f"{row['candidate_score']} | {row['delta_score']} | {row['base_total_cost']} | "
            f"{row['candidate_total_cost']} | {row['status']} |"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    for row in accepted:
        print(
            row["task_id"],
            row["primitive"],
            row["delta_score"],
            row["candidate_model_path"],
        )


if __name__ == "__main__":
    main()
