from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.experiment_db import EXPERIMENT_FIELDS, append_row
from neurogolf.onnx_build import build_zero_network
from neurogolf.paths import root
from neurogolf.reports import append_block
from neurogolf.submission import copy_onnx_files


EXP_ID = "GOLF_20260607_001_public_6154_repro"
SOURCE_ID = "SRC_KAGGLE_NOTEBOOK_OCTAVIO_6154"


def find_public_source() -> tuple[Path | None, str, str, str]:
    candidates = [
        (
            root("data/external/public_bundles/octaviograu_manual_rewrites_v205/extracted/submission"),
            SOURCE_ID,
            "octaviograu/neurogolf-manual-rewrites-v205",
            "public_6154_manual_rewrites",
        ),
        (
            root("data/external/public_bundles/jsrdcht_6029_submission_bundle/extracted"),
            "SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029",
            "jsrdcht/neurogolf-6029-submission-bundle",
            "public_6029_all_task",
        ),
    ]
    for path, source_id, dataset, method in candidates:
        if path.exists() and len(list(path.glob("task*.onnx"))) >= 300:
            return path, source_id, dataset, method
    return None, "SRC_LOCAL_ZERO_FALLBACK", "", "zero_fallback"


def main() -> None:
    source_dir, source_id, dataset_slug, method = find_public_source()
    exp_id = EXP_ID if source_id == SOURCE_ID else "GOLF_20260607_001_baseline_fallback"
    candidate = root("submissions/candidates", exp_id)
    onnx_dir = candidate / "onnx"
    candidate.mkdir(parents=True, exist_ok=True)

    if source_dir:
        copied = copy_onnx_files(source_dir, onnx_dir)
    else:
        copied = []
        for i in range(1, 401):
            path = onnx_dir / f"task{i:03d}.onnx"
            build_zero_network(path)
            copied.append(path)

    changed = candidate / "changed_tasks.csv"
    with changed.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "change"])
        writer.writeheader()
        for p in copied:
            writer.writerow({"task_id": p.stem, "change": method})

    source_trace = f"""# Source Trace

exp_id: {exp_id}
source_id: {source_id}
dataset_slug: {dataset_slug}
source_dir: {source_dir}
method: {method}
risk: low for public provenance, medium for relying on public bundle without new task-level diff yet
"""
    (candidate / "source_trace.md").write_text(source_trace, encoding="utf-8")

    manifest = {
        "exp_id": exp_id,
        "source_id": source_id,
        "dataset_slug": dataset_slug,
        "method": method,
        "onnx_dir": str(onnx_dir),
        "file_count": len(copied),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (candidate / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    exp_doc = f"""# {exp_id}

## Goal

Close the first submission loop by reproducing a public high-score ONNX bundle.

## Source basis
- source_id: {source_id}
- source type: public Kaggle dataset / notebook evidence
- why relevant: complete 400-task ONNX bundle with claimed public LB score

## Changes
- files changed: copied {len(copied)} ONNX files into candidate staging
- tasks changed: all available task files
- ONNX changes: none in this experiment
- algorithmic changes: public reproduction only

## Local validation
- command: python scripts/07_pack_submission.py --exp-id {exp_id}
- result: pending
- failed tasks: pending
- cost before: unknown
- cost after: pending

## Submission
- candidate path: submissions/candidates/{exp_id}
- notebook path: pending
- package hash: pending
- submitted: no
- Kaggle score: pending
- rank if known: pending

## Result analysis
- delta vs current best: pending

## Rollback / merge decision
- keep / rollback / isolate / retry: keep in queue if validator passes
- reason: first public reproducible baseline

## Next action
Run packer, build notebook, then submit from Kaggle Notebook output.
"""
    root("experiments", f"{exp_id}.md").write_text(exp_doc, encoding="utf-8")
    append_row(
        root("experiments/experiments.csv"),
        EXPERIMENT_FIELDS,
        {
            "exp_id": exp_id,
            "date": datetime.now().date().isoformat(),
            "lane": "A_public_highscore_absorb",
            "source_id": source_id,
            "goal": "first reproducible public bundle candidate",
            "changed_tasks": "all",
            "method": method,
            "local_valid": "pending",
            "status": "candidate_created",
            "next_action": "pack_and_validate",
        },
    )
    append_block(
        root("reports/SUBMISSION_ATTEMPTS.md"),
        f"""## {exp_id}

exp_id: {exp_id}
candidate_name: {method}
created_at: {datetime.now().isoformat(timespec="seconds")}
submission_path: submissions/candidates/{exp_id}/submission.zip
notebook_path: pending
changed_tasks: all
source_basis: {source_id}
expected_effect: reproduce public claimed score if Kaggle output matches source
local_validation: pending
local_score: pending
kaggle_submission_id:
kaggle_public_score:
status: queued_for_validation
rollback_decision:
notes: first-round candidate from public bundle
""",
    )
    print(candidate)


if __name__ == "__main__":
    main()

