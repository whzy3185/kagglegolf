from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from datetime import date, datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.aggressive_score import score_candidate, write_score_outputs
from neurogolf.evidence_gate import (
    load_config,
    parse_direction_registry,
    parse_evidence_registry,
    validate_row,
)
from neurogolf.experiment_db import EXPERIMENT_FIELDS
from neurogolf.notebook_builder import (
    build_kernel_metadata,
    build_submission_notebook,
)
from neurogolf.paths import root
from neurogolf.provenance import git_commit
from neurogolf.reports import append_block
from neurogolf.submission import copy_onnx_files, pack_submission_dir, write_manifest
from neurogolf.validation import validate_submission_dir


SOURCE_ID = "SRC_LOCAL_SUBMISSION1_ZIP"
DIRECTION_ID = "DIR_20260612_002_submission1_zip_diff_harvest"
PAPER_SOURCE_ID = "SRC_ARC_PRIZE_2024_REPORT"
OPEN_REPO_SOURCE_ID = "SRC_ARC_DSL_GITHUB"
HISTORICAL_SOURCE_ID = "SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP"
BASE_DATASET = "octaviograu/neurogolf-manual-rewrites-v205"


SUBMISSION_QUEUE_FIELDS = [
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

TASK_BANK_FIELDS = [
    "task_id",
    "differs_from_base",
    "zip_structural_ok",
    "zip_examples_checked",
    "zip_examples_passed",
    "zip_examples_failed",
    "excluded_from_full_reason",
    "excluded_from_chunk_reason",
    "selected_full",
    "selected_chunk_batch",
    "candidate_rank",
    "base_sha256",
    "zip_sha256",
    "source_model_path",
    "notes",
]

BATCH_RESULT_FIELDS = [
    "exp_id",
    "created_at",
    "batch_kind",
    "base_exp_id",
    "changed_task_count",
    "changed_tasks",
    "source_id",
    "local_valid",
    "examples_checked",
    "examples_failed",
    "evidence_gate_status",
    "aggressive_change_score",
    "aggressive_change_classification",
    "aggressive_change_gate_status",
    "submitted",
    "submission_id",
    "status",
    "public_score",
    "score_delta_vs_parent",
    "notes",
]


def task_id(index: int) -> str:
    return f"task{index:03d}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists() or not path.stat().st_size:
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def upsert_csv(path: Path, default_fields: list[str], key: str, row: dict) -> None:
    existing_fields, rows = read_csv(path)
    fields = list(existing_fields or default_fields)
    for field in default_fields + list(row):
        if field not in fields:
            fields.append(field)
    replaced = False
    for existing in rows:
        if existing.get(key) == row.get(key):
            existing.update(row)
            replaced = True
            break
    if not replaced:
        rows.append(row)
    write_csv(path, fields, rows)


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def current_best_exp_id() -> str:
    manifest_path = root("submissions/best/current_best_manifest.json")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return str(payload["exp_id"])


def resolve_base_candidate(base_exp_id: str) -> Path:
    candidate = root("submissions/candidates", base_exp_id)
    if not (candidate / "onnx").exists():
        raise SystemExit(f"Missing base candidate ONNX directory: {candidate / 'onnx'}")
    return candidate


def safe_refresh_dir(path: Path) -> None:
    resolved = path.resolve()
    allowed = root("data/interim").resolve()
    if not str(resolved).lower().startswith(str(allowed).lower() + "\\"):
        raise SystemExit(f"Refusing to delete outside data/interim: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def extract_zip(zip_path: Path, extract_dir: Path, *, refresh: bool) -> None:
    if refresh or not extract_dir.exists():
        safe_refresh_dir(extract_dir)
    else:
        extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        onnx_names = [name for name in archive.namelist() if name.endswith(".onnx")]
        for name in onnx_names:
            target = extract_dir / Path(name).name
            target.write_bytes(archive.read(name))
    files = sorted(extract_dir.glob("task*.onnx"))
    if len(files) != 400:
        raise SystemExit(f"Expected 400 ONNX files after extraction, found {len(files)}")


def load_or_validate_source(extract_dir: Path, validation_path: Path, examples_per_split: int) -> dict:
    if validation_path.exists() and validation_path.stat().st_size:
        payload = json.loads(validation_path.read_text(encoding="utf-8"))
        if int(payload.get("file_count", 0)) == 400:
            return payload
    payload = validate_submission_dir(
        extract_dir,
        root("data/raw/neurogolf-2026"),
        smoke_examples_per_split=examples_per_split,
    )
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def validation_by_task(payload: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for item in payload.get("results", []):
        task = item.get("task_id")
        if task:
            out[task] = item
    return out


def known_negative_tasks() -> set[str]:
    _, rows = read_csv(root("task_bank/task_submission_delta.csv"))
    rejected: set[str] = set()
    for row in rows:
        if row.get("attribution_strength") != "strong":
            continue
        decision = row.get("decision", "")
        if decision.startswith("rejected") or decision in {"negative_or_mixed"}:
            rejected.add(row.get("task_id", ""))
    return {item for item in rejected if item.startswith("task")}


def protected_current_best_tasks(base_exp_id: str) -> set[str]:
    manifest_path = root("submissions/candidates", base_exp_id, "manifest.json")
    if not manifest_path.exists():
        return set()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {str(item) for item in payload.get("changed_tasks", []) if str(item).startswith("task")}


def compare_tasks(base_dir: Path, extract_dir: Path, validation: dict) -> list[dict]:
    by_task = validation_by_task(validation)
    rows: list[dict] = []
    for index in range(1, 401):
        task = task_id(index)
        base_model = base_dir / f"{task}.onnx"
        zip_model = extract_dir / f"{task}.onnx"
        if not base_model.exists() or not zip_model.exists():
            raise SystemExit(f"Missing base or zip model for {task}")
        base_hash = sha256_file(base_model)
        zip_hash = sha256_file(zip_model)
        item = by_task.get(task, {})
        rows.append(
            {
                "task_id": task,
                "differs_from_base": str(base_hash != zip_hash).lower(),
                "zip_structural_ok": str(bool(item.get("ok"))).lower(),
                "zip_examples_checked": item.get("examples_checked", ""),
                "zip_examples_passed": item.get("examples_passed", ""),
                "zip_examples_failed": item.get("examples_failed", ""),
                "base_sha256": base_hash,
                "zip_sha256": zip_hash,
                "source_model_path": str(zip_model),
                "notes": "; ".join(item.get("structural_errors", [])[:2]),
            }
        )
    return rows


def gate_status(exp_id: str) -> dict:
    config = load_config(ROOT)
    sources = parse_evidence_registry(root("research/EVIDENCE_REGISTRY.md"))
    directions = parse_direction_registry(root("research/DIRECTION_REGISTRY.md"))
    return validate_row(
        {
            "exp_id": exp_id,
            "lane": "S_target_7800_submission_push",
            "direction_id": DIRECTION_ID,
            "leaderboard_source_id": SOURCE_ID,
            "paper_source_id": PAPER_SOURCE_ID,
            "open_repo_source_id": OPEN_REPO_SOURCE_ID,
            "historical_competition_source_id": HISTORICAL_SOURCE_ID,
        },
        config=config,
        sources=sources,
        directions=directions,
    )


def build_notebook(exp_id: str, candidate: Path) -> Path:
    notebook_path = root("notebooks/kaggle_submit_current.ipynb")
    build_submission_notebook(
        notebook_path,
        exp_id=exp_id,
        source_ids=[SOURCE_ID],
        dataset_slug=BASE_DATASET,
        source_subdir="submission",
        git_commit=git_commit(),
        embedded_zip_path=candidate / "submission.zip",
    )
    build_kernel_metadata(
        root("notebooks/kernel-metadata.json"),
        notebook_path.name,
        [BASE_DATASET],
    )
    shutil.copy2(notebook_path, candidate / "notebook.ipynb")
    return candidate / "notebook.ipynb"


def write_task_list(path: Path, tasks: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(tasks) + "\n", encoding="utf-8")


def write_source_trace(
    candidate: Path,
    *,
    exp_id: str,
    base_exp_id: str,
    tasks: list[str],
    batch_kind: str,
    invalid_tasks: list[str],
) -> None:
    lines = [
        f"# {exp_id} Source Trace",
        "",
        f"direction_id: {DIRECTION_ID}",
        f"primary_source_id: {SOURCE_ID}",
        f"base_exp_id: {base_exp_id}",
        f"batch_kind: {batch_kind}",
        "",
        "leaderboard_basis:",
        f"  source_id: {SOURCE_ID}",
        "  reason: Local submission (1).zip is user-reported above current best; only locally valid task-level diffs are harvested.",
        "",
        "paper_basis:",
        f"  source_id: {PAPER_SOURCE_ID}",
        "  reason: ARC Prize report supports exact example validation before hidden-set feedback.",
        "",
        "open_repo_basis:",
        f"  source_id: {OPEN_REPO_SOURCE_ID}",
        "  reason: ARC-DSL semantics support grouping and interpreting task-level replacement behavior.",
        "",
        "historical_competition_basis:",
        f"  source_id: {HISTORICAL_SOURCE_ID}",
        "  reason: Prior code-golf workflow supports repeated task-level harvesting and leaderboard ablation.",
        "",
        f"invalid_source_tasks_excluded: {','.join(invalid_tasks) if invalid_tasks else 'none'}",
        f"changed_task_count: {len(tasks)}",
        f"changed_tasks: {','.join(tasks)}",
        "",
    ]
    (candidate / "source_trace.md").write_text("\n".join(lines), encoding="utf-8")


def build_candidate(
    *,
    exp_id: str,
    batch_kind: str,
    base_exp_id: str,
    base_candidate: Path,
    extract_dir: Path,
    tasks: list[str],
    invalid_tasks: list[str],
    examples_per_split: int,
    score_aggressive: bool,
) -> dict:
    gate = gate_status(exp_id)
    if gate["status"] != "pass":
        raise SystemExit(f"Evidence gate failed for {exp_id}: {'; '.join(gate['reasons'])}")

    candidate = root("submissions/candidates", exp_id)
    target = candidate / "onnx"
    copy_onnx_files(base_candidate / "onnx", target)
    changed_rows = []
    for task in tasks:
        src = extract_dir / f"{task}.onnx"
        dst = target / f"{task}.onnx"
        shutil.copy2(src, dst)
        changed_rows.append(
            {
                "task_id": task,
                "model_path": str(src),
                "source_id": SOURCE_ID,
                "method_family": "submission1_zip_diff",
                "risk": "medium",
                "cost_proxy": "",
            }
        )

    write_csv(
        candidate / "changed_tasks.csv",
        ["task_id", "model_path", "source_id", "method_family", "risk", "cost_proxy"],
        changed_rows,
    )
    write_source_trace(
        candidate,
        exp_id=exp_id,
        base_exp_id=base_exp_id,
        tasks=tasks,
        batch_kind=batch_kind,
        invalid_tasks=invalid_tasks,
    )
    (candidate / "risk.md").write_text(
        "# Risk\n\nrisk: medium\nreason: local artifact task-level diff; raw full zip has invalid task019/task233 and is not directly submitted.\n",
        encoding="utf-8",
    )

    validation = validate_submission_dir(
        target,
        root("data/raw/neurogolf-2026"),
        smoke_examples_per_split=examples_per_split,
    )
    (candidate / "local_validation.json").write_text(
        json.dumps(validation, indent=2),
        encoding="utf-8",
    )
    package = pack_submission_dir(target, candidate / "submission.zip")
    notebook_path = build_notebook(exp_id, candidate)

    manifest = {
        "exp_id": exp_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base": str(base_candidate),
        "base_exp_id": base_exp_id,
        "parent_exp_id": base_exp_id,
        "source_id": SOURCE_ID,
        "primary_source_id": SOURCE_ID,
        "direction_id": DIRECTION_ID,
        "leaderboard_source_id": SOURCE_ID,
        "paper_source_id": PAPER_SOURCE_ID,
        "open_repo_source_id": OPEN_REPO_SOURCE_ID,
        "historical_competition_source_id": HISTORICAL_SOURCE_ID,
        "evidence_gate_status": gate["status"],
        "evidence_gate_notes": "; ".join(gate["reasons"]),
        "risk": "medium",
        "batch_kind": batch_kind,
        "changed_tasks": tasks,
        "changed_task_count": len(tasks),
        "invalid_source_tasks_excluded": invalid_tasks,
        "validation_ok": validation.get("ok_for_submission_queue", False),
        "examples_checked": validation.get("examples_checked", 0),
        "examples_failed": validation.get("examples_failed", 0),
        **package,
    }
    write_manifest(candidate / "manifest.json", manifest)

    local_valid = str(validation.get("ok_for_submission_queue", False)).lower()
    status = "queued_for_submit" if truthy(local_valid) else "failed_local_validation"
    next_action = "submit_notebook_output" if truthy(local_valid) else "inspect_validation"
    upsert_csv(
        root("experiments/experiments.csv"),
        EXPERIMENT_FIELDS,
        "exp_id",
        {
            "exp_id": exp_id,
            "date": date.today().isoformat(),
            "lane": "S_target_7800_submission_push",
            "direction_id": DIRECTION_ID,
            "leaderboard_source_id": SOURCE_ID,
            "paper_source_id": PAPER_SOURCE_ID,
            "open_repo_source_id": OPEN_REPO_SOURCE_ID,
            "historical_competition_source_id": HISTORICAL_SOURCE_ID,
            "source_id": SOURCE_ID,
            "goal": "harvest locally valid task-level diffs from submission (1).zip",
            "changed_tasks": ",".join(tasks),
            "method": "submission1_zip_diff_batch",
            "local_valid": local_valid,
            "status": status,
            "next_action": next_action,
        },
    )
    upsert_csv(
        root("experiments/submission_queue.csv"),
        SUBMISSION_QUEUE_FIELDS,
        "exp_id",
        {
            "exp_id": exp_id,
            "candidate_path": str(candidate),
            "risk": "medium",
            "direction_id": DIRECTION_ID,
            "leaderboard_source_id": SOURCE_ID,
            "paper_source_id": PAPER_SOURCE_ID,
            "open_repo_source_id": OPEN_REPO_SOURCE_ID,
            "historical_competition_source_id": HISTORICAL_SOURCE_ID,
            "source_id": SOURCE_ID,
            "evidence_gate_status": gate["status"],
            "duplicate_hash": "false",
            "aggressive_change_score": "",
            "aggressive_change_classification": "unscored",
            "aggressive_change_gate_status": "pending",
            "changed_tasks": ",".join(tasks),
            "local_valid": local_valid,
            "notebook_ready": str(notebook_path.exists()).lower(),
            "submitted": "false",
            "status": status,
            "next_action": next_action,
            "task_attribution_status": "pending_lb_feedback",
        },
    )
    upsert_csv(
        root("experiments/notebook_queue.csv"),
        NOTEBOOK_QUEUE_FIELDS,
        "exp_id",
        {
            "exp_id": exp_id,
            "notebook_path": str(notebook_path),
            "dataset_path": "embedded_submission_zip",
            "output_expected": "submission.zip",
            "kernel_slug": "muelsyse111/neurogolf-submit-current",
            "kernel_status": "not_pushed",
            "output_verified": "false",
            "output_sha256": package["sha256"],
            "ready_for_submit": str(notebook_path.exists() and truthy(local_valid)).lower(),
            "notes": "Notebook embeds candidate zip.",
        },
    )
    append_block(
        root("reports/SUBMISSION_ATTEMPTS.md"),
        f"""## {exp_id}

created_at: {datetime.now().isoformat(timespec="seconds")}
submission_path: submissions/candidates/{exp_id}/submission.zip
notebook_path: {notebook_path}
changed_tasks: {','.join(tasks)}
source_basis: {SOURCE_ID}
batch_kind: {batch_kind}
local_validation: {'pass' if truthy(local_valid) else 'fail'}
examples_checked: {validation.get('examples_checked', '')}
examples_failed: {validation.get('examples_failed', '')}
status: {status}
risk: medium
notes: generated by submission1 diff batch harvester
""",
    )

    ags_payload: dict = {}
    if score_aggressive and truthy(local_valid):
        ags_payload = score_candidate(ROOT, exp_id)
        write_score_outputs(ROOT, ags_payload)

    return {
        "exp_id": exp_id,
        "created_at": manifest["created_at"],
        "batch_kind": batch_kind,
        "base_exp_id": base_exp_id,
        "changed_task_count": len(tasks),
        "changed_tasks": ",".join(tasks),
        "source_id": SOURCE_ID,
        "local_valid": local_valid,
        "examples_checked": validation.get("examples_checked", ""),
        "examples_failed": validation.get("examples_failed", ""),
        "evidence_gate_status": gate["status"],
        "aggressive_change_score": f"{ags_payload.get('ags', ''):.6f}" if ags_payload else "",
        "aggressive_change_classification": ags_payload.get("classification", "") if ags_payload else "",
        "aggressive_change_gate_status": "pass"
        if ags_payload.get("submission_gate_pass")
        else ("pending" if not ags_payload else "fail"),
        "submitted": "false",
        "submission_id": "",
        "status": status,
        "public_score": "",
        "score_delta_vs_parent": "",
        "notes": "built from submission (1).zip; invalid source tasks excluded",
    }


def write_report(
    *,
    base_exp_id: str,
    source_validation: dict,
    diff_count: int,
    full_tasks: list[str],
    chunk_tasks: list[str],
    invalid_tasks: list[str],
    batch_rows: list[dict],
) -> None:
    lines = [
        "# Submission1 Diff Harvest",
        "",
        f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"source_id: {SOURCE_ID}",
        f"base_exp_id: {base_exp_id}",
        f"source_file_count: {source_validation.get('file_count', '')}",
        f"source_examples_checked: {source_validation.get('examples_checked', '')}",
        f"source_examples_failed: {source_validation.get('examples_failed', '')}",
        f"source_ok_for_direct_submission: {str(source_validation.get('ok_for_submission_queue', '')).lower()}",
        f"invalid_source_tasks_excluded: {','.join(invalid_tasks) if invalid_tasks else 'none'}",
        f"diff_count_vs_base: {diff_count}",
        f"full_valid_diff_task_count: {len(full_tasks)}",
        f"chunk_pool_task_count: {len(chunk_tasks)}",
        "",
        "## Batch Candidates",
        "",
        "| exp_id | kind | tasks | local_valid | AGS | AGS class | gate | status |",
        "|---|---|---:|---|---:|---|---|---|",
    ]
    for row in batch_rows:
        lines.append(
            f"| {row['exp_id']} | {row['batch_kind']} | {row['changed_task_count']} | "
            f"{row['local_valid']} | {row['aggressive_change_score']} | "
            f"{row['aggressive_change_classification']} | {row['aggressive_change_gate_status']} | {row['status']} |"
        )
    if not batch_rows:
        lines.append("| none | none | 0 |  |  |  |  |  |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Raw submission (1).zip is retained as an ignored local artifact and is not committed.",
            "- Full harvest replaces all locally valid diffs and keeps current-best task019/task233.",
            "- Chunk batches exclude current-best protected tasks and known strong negative single-task probes.",
            "",
        ]
    )
    root("reports/SUBMISSION1_DIFF_HARVEST.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip-path", default="submission (1).zip")
    parser.add_argument("--extract-dir", default="data/interim/submission1_compare")
    parser.add_argument("--validation-json", default="reports/SUBMISSION1_LOCAL_VALIDATION.json")
    parser.add_argument("--base-exp-id", default="")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--batch-count", type=int, default=4)
    parser.add_argument("--examples-per-split", type=int, default=10000)
    parser.add_argument("--source-validation-examples-per-split", type=int, default=10000)
    parser.add_argument("--refresh-extract", action="store_true")
    parser.add_argument("--skip-full", action="store_true")
    parser.add_argument("--no-score-aggressive", action="store_true")
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    if not zip_path.is_absolute():
        zip_path = ROOT / zip_path
    if not zip_path.exists():
        raise SystemExit(f"Missing source zip: {zip_path}")

    extract_dir = Path(args.extract_dir)
    if not extract_dir.is_absolute():
        extract_dir = ROOT / extract_dir
    extract_zip(zip_path, extract_dir, refresh=args.refresh_extract)

    base_exp_id = args.base_exp_id or current_best_exp_id()
    base_candidate = resolve_base_candidate(base_exp_id)
    base_dir = base_candidate / "onnx"

    validation_path = Path(args.validation_json)
    if not validation_path.is_absolute():
        validation_path = ROOT / validation_path
    source_validation = load_or_validate_source(
        extract_dir,
        validation_path,
        args.source_validation_examples_per_split,
    )
    task_rows = compare_tasks(base_dir, extract_dir, source_validation)
    diff_rows = [row for row in task_rows if truthy(row["differs_from_base"])]
    invalid_tasks = [
        row["task_id"]
        for row in task_rows
        if truthy(row["differs_from_base"]) and not truthy(row["zip_structural_ok"])
    ]
    known_negatives = known_negative_tasks()
    protected = protected_current_best_tasks(base_exp_id)

    full_tasks = [
        row["task_id"]
        for row in diff_rows
        if row["task_id"] not in set(invalid_tasks)
    ]
    chunk_tasks = [
        row["task_id"]
        for row in diff_rows
        if row["task_id"] not in set(invalid_tasks)
        and row["task_id"] not in known_negatives
        and row["task_id"] not in protected
    ]

    batch_specs: list[tuple[str, str, list[str]]] = []
    if not args.skip_full:
        batch_specs.append(("GOLF_20260612_094_submission1_valid153_full", "full_valid_diff", full_tasks))
    for batch_index in range(args.batch_count):
        start = batch_index * args.batch_size
        tasks = chunk_tasks[start : start + args.batch_size]
        if not tasks:
            break
        label = chr(ord("A") + batch_index)
        exp_num = 95 + batch_index
        batch_specs.append((f"GOLF_20260612_{exp_num:03d}_submission1_diff_{label}{len(tasks)}", f"chunk_{label}", tasks))

    selected_batch_by_task: dict[str, str] = {}
    rank_by_task: dict[str, int] = {}
    rank = 1
    for exp_id, _, tasks in batch_specs:
        write_task_list(root("task_bank", f"{exp_id}.txt"), tasks)
        for task in tasks:
            selected_batch_by_task.setdefault(task, exp_id)
            rank_by_task.setdefault(task, rank)
            rank += 1

    invalid_set = set(invalid_tasks)
    full_set = set(full_tasks)
    chunk_set = set(chunk_tasks)
    for row in task_rows:
        task = row["task_id"]
        full_reason = ""
        chunk_reason = ""
        if not truthy(row["differs_from_base"]):
            full_reason = "same_as_base"
            chunk_reason = "same_as_base"
        elif task in invalid_set:
            full_reason = "source_structural_invalid"
            chunk_reason = "source_structural_invalid"
        elif task not in full_set:
            full_reason = "not_selected"
        if task in known_negatives:
            chunk_reason = "known_strong_negative_probe"
        elif task in protected:
            chunk_reason = "protected_current_best_task"
        elif task not in chunk_set and not chunk_reason:
            chunk_reason = "outside_chunk_limit"
        row.update(
            {
                "excluded_from_full_reason": full_reason,
                "excluded_from_chunk_reason": chunk_reason,
                "selected_full": str(task in full_set).lower(),
                "selected_chunk_batch": selected_batch_by_task.get(task, ""),
                "candidate_rank": rank_by_task.get(task, ""),
            }
        )
    write_csv(root("task_bank/submission1_diff_task_bank.csv"), TASK_BANK_FIELDS, task_rows)

    built_rows: list[dict] = []
    for exp_id, batch_kind, tasks in batch_specs:
        if not tasks:
            continue
        built_rows.append(
            build_candidate(
                exp_id=exp_id,
                batch_kind=batch_kind,
                base_exp_id=base_exp_id,
                base_candidate=base_candidate,
                extract_dir=extract_dir,
                tasks=tasks,
                invalid_tasks=invalid_tasks,
                examples_per_split=args.examples_per_split,
                score_aggressive=not args.no_score_aggressive,
            )
        )

    existing_results = read_csv(root("task_bank/submission1_diff_batch_results.csv"))[1]
    by_exp = {row.get("exp_id", ""): row for row in existing_results}
    for row in built_rows:
        by_exp[row["exp_id"]] = row
    write_csv(
        root("task_bank/submission1_diff_batch_results.csv"),
        BATCH_RESULT_FIELDS,
        [by_exp[key] for key in sorted(by_exp)],
    )
    write_report(
        base_exp_id=base_exp_id,
        source_validation=source_validation,
        diff_count=len(diff_rows),
        full_tasks=full_tasks,
        chunk_tasks=chunk_tasks,
        invalid_tasks=invalid_tasks,
        batch_rows=built_rows,
    )

    print(f"base_exp_id={base_exp_id}")
    print(f"diff_count={len(diff_rows)}")
    print(f"invalid_source_tasks={','.join(invalid_tasks)}")
    print(f"full_valid_diff_task_count={len(full_tasks)}")
    print(f"chunk_pool_task_count={len(chunk_tasks)}")
    print("built_exp_ids=" + ",".join(row["exp_id"] for row in built_rows))


if __name__ == "__main__":
    main()
