from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import date, datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.experiment_db import EXPERIMENT_FIELDS, append_row
from neurogolf.notebook_builder import (
    build_kernel_metadata,
    build_overlay_submission_notebook,
    build_submission_notebook,
)
from neurogolf.paths import root
from neurogolf.provenance import git_commit
from neurogolf.reports import append_block
from neurogolf.submission import copy_onnx_files, pack_submission_dir, write_manifest
from neurogolf.validation import validate_submission_dir, write_validation


SUBMISSION_QUEUE_FIELDS = [
    "exp_id",
    "candidate_path",
    "risk",
    "source_id",
    "changed_tasks",
    "local_valid",
    "notebook_ready",
    "submitted",
    "submission_id",
    "public_score",
    "status",
    "next_action",
]

NOTEBOOK_QUEUE_FIELDS = [
    "exp_id",
    "notebook_path",
    "dataset_path",
    "output_expected",
    "kernel_slug",
    "kernel_status",
    "output_verified",
    "output_sha256",
    "ready_for_submit",
    "notes",
]

SOURCE_DATASETS = {
    "SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029": ("jsrdcht/neurogolf-6029-submission-bundle", ""),
    "SRC_KAGGLE_NOTEBOOK_BEICICC_6645": ("beicicc/neurogolf-6645-39-open-submission-artifact", ""),
    "SRC_KAGGLE_NOTEBOOK_VYANKTESH_MULTI_SOURCE": ("vyankteshdwivedi/neurogolf-multi-source-onnx-solver", ""),
}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root(str(path))


def source_exists(source_id: str) -> bool:
    text = root("research/EVIDENCE_REGISTRY.md").read_text(encoding="utf-8")
    return f"source_id: {source_id}" in text


def base_onnx_dir(base: str) -> Path:
    path = resolve_path(base)
    return path / "onnx" if (path / "onnx").exists() else path


def task_name(value: str) -> str:
    stem = value[:-5] if value.endswith(".onnx") else value
    if stem.startswith("task"):
        return stem
    return f"task{int(stem):03d}"


def resolve_full_replace_overrides(path: Path, risk: str) -> list[dict]:
    files = sorted(path.glob("task*.onnx"))
    by_name = {p.stem: p for p in files}
    official_names = [f"task{i:03d}" for i in range(1, 401)]
    zero_based_names = [f"task{i:03d}" for i in range(0, 400)]

    if all(name in by_name for name in official_names):
        return [
            {
                "task_id": name,
                "model_path": str(by_name[name]),
                "method_family": "public_full_replace",
                "cost_proxy": "",
                "risk": risk,
            }
            for name in official_names
        ]

    if all(name in by_name for name in zero_based_names):
        overrides = []
        for idx, name in enumerate(zero_based_names, start=1):
            overrides.append(
                {
                    "task_id": f"task{idx:03d}",
                    "model_path": str(by_name[name]),
                    "method_family": "public_full_replace_zero_based",
                    "cost_proxy": "",
                    "risk": risk,
                }
            )
        return overrides

    raise SystemExit(
        f"--full-replace-dir requires either official task001-task400 files or zero-based task000-task399 files; found {len(files)} task files in {path}"
    )


def read_overrides(path: Path, top_k: int | None) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows = [r for r in rows if str(r.get("local_valid", "")).lower() in {"true", "1", "yes"}]
    rows.sort(key=lambda r: int(r.get("candidate_rank") or 999999))
    return rows[:top_k] if top_k else rows


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def upsert_csv(path: Path, fields: list[str], key: str, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    if path.exists() and path.stat().st_size:
        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    replaced = False
    for existing in rows:
        if existing.get(key) == row.get(key):
            existing.update(row)
            replaced = True
            break
    if not replaced:
        rows.append(row)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in fields} for r in rows)


def build_notebook(exp_id: str, candidate: Path, source_ids: list[str], changed_tasks: list[str]) -> Path:
    notebook_path = root("notebooks/kaggle_submit_current.ipynb")
    dataset_sources = ["octaviograu/neurogolf-manual-rewrites-v205"]
    source_id = source_ids[0]
    if source_id in SOURCE_DATASETS and changed_tasks:
        overlay_slug, overlay_subdir = SOURCE_DATASETS[source_id]
        build_overlay_submission_notebook(
            notebook_path,
            exp_id=exp_id,
            source_ids=source_ids,
            git_commit=git_commit(),
            base_dataset_slug="octaviograu/neurogolf-manual-rewrites-v205",
            base_source_subdir="submission",
            overlay_dataset_slug=overlay_slug,
            overlay_source_subdir=overlay_subdir,
            changed_tasks=changed_tasks,
        )
        dataset_sources.append(overlay_slug)
    else:
        build_submission_notebook(
            notebook_path,
            exp_id=exp_id,
            source_ids=source_ids,
            dataset_slug="octaviograu/neurogolf-manual-rewrites-v205",
            source_subdir="submission",
            git_commit=git_commit(),
            embedded_zip_path=candidate / "submission.zip",
        )
    build_kernel_metadata(root("notebooks/kernel-metadata.json"), notebook_path.name, dataset_sources)
    shutil.copy2(notebook_path, candidate / "notebook.ipynb")
    return candidate / "notebook.ipynb"


def update_task_bank(changed: list[dict], exp_id: str, source_id: str, risk: str, validation_ok: bool) -> None:
    status_path = root("task_bank/task_status.csv")
    best_path = root("task_bank/best_by_task.csv")
    if not status_path.exists() or not best_path.exists():
        return

    changed_by_task = {row["task_id"]: row for row in changed}
    with status_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        status_rows = list(reader)
        status_fields = reader.fieldnames or []
    for row in status_rows:
        if row["task_id"] in changed_by_task:
            item = changed_by_task[row["task_id"]]
            row.update(
                {
                    "has_solution": "true",
                    "correct_on_official_examples": str(validation_ok).lower(),
                    "source_id": source_id,
                    "method_family": item.get("method_family", "override"),
                    "model_path": item["model_path"],
                    "last_exp_id": exp_id,
                    "risk": risk,
                    "notes": f"override candidate generated {datetime.now().isoformat(timespec='seconds')}",
                }
            )
    with status_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=status_fields)
        writer.writeheader()
        writer.writerows(status_rows)

    with best_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        best_rows = list(reader)
        best_fields = reader.fieldnames or []
    for row in best_rows:
        if row["task_id"] in changed_by_task:
            item = changed_by_task[row["task_id"]]
            row.update(
                {
                    "best_model_path": item["model_path"],
                    "source_id": source_id,
                    "method": item.get("method_family", "override"),
                    "local_correct": str(validation_ok).lower(),
                    "local_cost": item.get("cost_proxy", ""),
                    "last_changed_exp_id": exp_id,
                    "status": "candidate",
                    "notes": f"risk={risk}; pending LB delta",
                }
            )
    with best_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=best_fields)
        writer.writeheader()
        writer.writerows(best_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--override-csv", default="")
    parser.add_argument("--full-replace-dir", default="")
    parser.add_argument("--top-k", type=int, default=0)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--risk", choices=["low", "medium", "high"], required=True)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--pack", action="store_true")
    parser.add_argument("--build-notebook", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()

    if not source_exists(args.source_id):
        raise SystemExit(f"Unknown source_id: {args.source_id}")

    overrides: list[dict] = []
    if args.full_replace_dir:
        replace_dir = resolve_path(args.full_replace_dir)
        overrides.extend(resolve_full_replace_overrides(replace_dir, args.risk))
    elif args.override_csv:
        for row in read_overrides(resolve_path(args.override_csv), args.top_k or None):
            overrides.append(
                {
                    "task_id": task_name(row["task_id"]),
                    "model_path": row["candidate_model_path"],
                    "method_family": row.get("method_family", "csv_override"),
                    "cost_proxy": row.get("cost_proxy", ""),
                    "risk": row.get("risk", args.risk),
                }
            )
    elif args.task and args.model:
        overrides.append(
            {
                "task_id": task_name(args.task),
                "model_path": str(resolve_path(args.model)),
                "method_family": "single_task_override",
                "cost_proxy": "",
                "risk": args.risk,
            }
        )
    else:
        raise SystemExit("Provide either --task/--model or --override-csv")

    candidate = root("submissions/candidates", args.exp_id)
    target = candidate / "onnx"
    copy_onnx_files(base_onnx_dir(args.base), target)
    changed = []
    for item in overrides:
        src = resolve_path(item["model_path"])
        dst = target / f"{item['task_id']}.onnx"
        shutil.copy2(src, dst)
        changed.append({**item, "model_path": str(src)})

    changed_csv = candidate / "changed_tasks.csv"
    write_csv(changed_csv, ["task_id", "model_path", "source_id", "method_family", "risk", "cost_proxy"], [{**r, "source_id": args.source_id} for r in changed])
    (candidate / "source_trace.md").write_text(
        "\n".join(
            [
                f"# {args.exp_id} Source Trace",
                "",
                f"source_id: {args.source_id}",
                "parent_exp_id: GOLF_20260607_001_public_6154_repro",
                f"changed_tasks: {','.join(r['task_id'] for r in changed)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (candidate / "risk.md").write_text(
        f"# Risk\n\nrisk: {args.risk}\nreason: public source override; high-risk entries are isolated from best until LB confirms value.\n",
        encoding="utf-8",
    )

    validation = {}
    if args.validate:
        validation = validate_submission_dir(target, root("data/raw/neurogolf-2026"), smoke_examples_per_split=1)
        write_validation(candidate / "local_validation.json", validation)

    manifest = {
        "exp_id": args.exp_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base": args.base,
        "source_id": args.source_id,
        "risk": args.risk,
        "changed_tasks": [r["task_id"] for r in changed],
        "changed_task_count": len(changed),
        "validation_ok": validation.get("ok_for_submission_queue", ""),
    }
    if args.pack:
        manifest.update(pack_submission_dir(target, candidate / "submission.zip"))
    write_manifest(candidate / "manifest.json", manifest)

    notebook_path = ""
    if args.build_notebook:
        notebook_path = str(build_notebook(args.exp_id, candidate, [args.source_id], [r["task_id"] for r in changed]))

    local_valid = str(validation.get("ok_for_submission_queue", "")).lower()
    if args.record:
        upsert_csv(
            root("experiments/experiments.csv"),
            EXPERIMENT_FIELDS,
            "exp_id",
            {
                "exp_id": args.exp_id,
                "date": date.today().isoformat(),
                "lane": "S_target_7000_submission_push",
                "source_id": args.source_id,
                "goal": "submit source-backed task override candidate toward 7000+ target",
                "changed_tasks": ",".join(r["task_id"] for r in changed),
                "method": "task_override",
                "local_valid": local_valid,
                "status": "queued_for_submit" if validation.get("ok_for_submission_queue") else "failed_local_validation",
                "next_action": "submit_queue" if validation.get("ok_for_submission_queue") else "inspect_validation",
            },
        )
        append_block(
            root("reports/SUBMISSION_ATTEMPTS.md"),
            f"""## {args.exp_id}

created_at: {datetime.now().isoformat(timespec="seconds")}
submission_path: submissions/candidates/{args.exp_id}/submission.zip
notebook_path: {notebook_path}
changed_tasks: {','.join(r['task_id'] for r in changed)}
source_basis: {args.source_id}
local_validation: {'pass' if validation.get('ok_for_submission_queue') else 'fail'}
examples_checked: {validation.get('examples_checked', '')}
examples_failed: {validation.get('examples_failed', '')}
status: {'queued_for_submit' if validation.get('ok_for_submission_queue') else 'failed_local_validation'}
risk: {args.risk}
notes: generated by submit-ready task override pipeline
""",
        )
        upsert_csv(
            root("experiments/submission_queue.csv"),
            SUBMISSION_QUEUE_FIELDS,
            "exp_id",
            {
                "exp_id": args.exp_id,
                "candidate_path": str(candidate),
                "risk": args.risk,
                "source_id": args.source_id,
                "changed_tasks": ",".join(r["task_id"] for r in changed),
                "local_valid": local_valid,
                "notebook_ready": str(bool(notebook_path)).lower(),
                "submitted": "false",
                "status": "queued_for_submit" if validation.get("ok_for_submission_queue") else "failed_local_validation",
                "next_action": "submit_notebook_output" if validation.get("ok_for_submission_queue") else "inspect_validation",
            },
        )
        upsert_csv(
            root("experiments/notebook_queue.csv"),
            NOTEBOOK_QUEUE_FIELDS,
            "exp_id",
            {
                "exp_id": args.exp_id,
                "notebook_path": notebook_path,
                "dataset_path": "embedded_submission_zip",
                "output_expected": "submission.zip",
                "kernel_slug": "muelsyse111/neurogolf-submit-current",
                "kernel_status": "not_pushed",
                "output_verified": "false",
                "ready_for_submit": str(bool(notebook_path and validation.get("ok_for_submission_queue"))).lower(),
                "notes": "Notebook embeds candidate zip.",
            },
        )
        update_task_bank(changed, args.exp_id, args.source_id, args.risk, bool(validation.get("ok_for_submission_queue")))

    print(candidate)
    print("changed_tasks", ",".join(r["task_id"] for r in changed))
    print("validation_ok", validation.get("ok_for_submission_queue", "not_run"))


if __name__ == "__main__":
    main()
