from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path

import yaml

from _bootstrap import ROOT
from neurogolf.aggressive_score import score_candidate, write_score_outputs
from neurogolf.evidence_gate import (
    update_candidate_manifest,
    update_submission_queue,
    validate_experiments,
    write_gate_outputs,
)
from neurogolf.notebook_builder import build_kernel_metadata, build_submission_notebook
from neurogolf.paths import root
from neurogolf.provenance import git_commit
from neurogolf.reports import append_block
from neurogolf.simple_exact import BANK_FIELDS, load_bank, parse_params, rel, write_csv
from neurogolf.submission import copy_onnx_files, pack_submission_dir, write_manifest
from neurogolf.validation import validate_submission_dir, write_validation


DIRECTION_ID = "DIR_20260610_001_simple_exact_batch_replacement"
LEADERBOARD_SOURCE_ID = "SRC_DISCUSSION_AGENT_HARNESS_6580"
PAPER_SOURCE_ID = "SRC_ARC_PRIZE_2024_REPORT"
OPEN_REPO_SOURCE_ID = "SRC_ARC_DSL_GITHUB"
HISTORICAL_SOURCE_ID = "SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP"
SOURCE_ID = "SRC_ARC_DSL_GITHUB"

EXPERIMENT_FIELDS = [
    "exp_id",
    "date",
    "lane",
    "direction_id",
    "leaderboard_source_id",
    "paper_source_id",
    "open_repo_source_id",
    "historical_competition_source_id",
    "source_id",
    "goal",
    "changed_tasks",
    "method",
    "local_valid",
    "local_score",
    "lb_score",
    "delta_vs_best",
    "status",
    "rollback_reason",
    "next_action",
]

QUEUE_FIELDS = [
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


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists() or not path.stat().st_size:
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def upsert_csv(path: Path, default_fields: list[str], key: str, row: dict) -> None:
    fields, rows = read_csv(path)
    if not fields:
        fields = list(default_fields)
    for field in default_fields:
        if field not in fields:
            fields.append(field)
    for field in row:
        if field not in fields:
            fields.append(field)
    replaced = False
    for item in rows:
        if item.get(key) == row.get(key):
            item.update(row)
            replaced = True
            break
    if not replaced:
        rows.append(row)
    write_csv(path, fields, rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_candidate(exp_id_or_path: str) -> Path:
    path = Path(exp_id_or_path)
    if path.exists():
        return path
    return root("submissions/candidates", exp_id_or_path)


def load_policy() -> dict:
    path = root("configs/simple_exact_batch.yaml")
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def infer_group(exp_id: str, batch_size: int) -> str:
    lowered = exp_id.lower()
    if "conservative" in lowered:
        return "conservative"
    if "medium" in lowered:
        return "medium"
    if "aggressive" in lowered:
        return "aggressive"
    if batch_size <= 5:
        return "conservative"
    if batch_size <= 10:
        return "medium"
    return "aggressive"


def family_aliases(row: dict) -> set[str]:
    rule_name = row.get("rule_name", "")
    family = row.get("rule_family", "")
    aliases = {rule_name, family}
    if rule_name in {"horizontal_mirror", "vertical_mirror"}:
        aliases.add("mirror")
    if rule_name == "crop_nonzero_bbox":
        aliases.add("crop_bbox")
    if rule_name in {"largest_color_crop", "largest_object_crop", "least_color_crop"}:
        aliases.add("object_crop")
    if rule_name == "most_color_canvas":
        aliases.add("color_canvas")
    if rule_name in {"fill_bounding_box", "frontier_fill"}:
        aliases.add("simple_fill")
    if rule_name == "hconcat_self":
        aliases.add("hconcat")
    if rule_name == "vconcat_self":
        aliases.add("vconcat")
    if rule_name in {"upscale_x2", "upscale_x3"}:
        aliases.add("upscale")
    return aliases


def allowed_by_group(row: dict, group: str, policy: dict) -> bool:
    groups = policy.get("batch_groups", {})
    config = groups.get(group, {})
    include_only = set(config.get("include_only") or [])
    include = set(config.get("include") or [])
    aliases = family_aliases(row)
    if "all_simple_exact_tasks" in include:
        return True
    if include_only:
        return bool(include_only & aliases)
    if include:
        return bool(include & aliases)
    return True


def selected_bank_rows(args: argparse.Namespace, base_dir: Path) -> list[dict]:
    policy = load_policy()
    rows = [
        row
        for row in load_bank()
        if row.get("eligible_for_batch", "").lower() == "true"
        and row.get("train_pass_rate") == "1.0"
        and row.get("candidate_onnx_path")
    ]
    by_task: dict[str, list[dict]] = {}
    for row in rows:
        by_task.setdefault(row["task_id"], []).append(row)

    if args.task_list:
        tasks = [
            line.strip()
            for line in Path(args.task_list).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        ordered = []
        for task_id in tasks:
            choices = by_task.get(task_id, [])
            if choices:
                ordered.append(choices[0])
    else:
        group = infer_group(args.exp_id, args.batch_size)
        ordered = [
            row
            for row in rows
            if allowed_by_group(row, group, policy)
        ]
        ordered.sort(
            key=lambda row: (
                row.get("estimated_hidden_risk") != "low",
                int(row["task_id"][-3:]),
                row.get("rule_name", ""),
            )
        )

    selected: list[dict] = []
    seen: set[str] = set()
    max_tasks = args.max_tasks or args.batch_size
    for row in ordered:
        task_id = row["task_id"]
        if task_id in seen:
            continue
        onnx_path = ROOT / row["candidate_onnx_path"]
        base_path = base_dir / f"{task_id}.onnx"
        if not onnx_path.exists() or not base_path.exists():
            continue
        if sha256(onnx_path) == sha256(base_path):
            continue
        selected.append(row)
        seen.add(task_id)
        if max_tasks and len(selected) >= max_tasks:
            break
    return selected


def ensure_direction(exp_id: str) -> None:
    path = root("research/DIRECTION_REGISTRY.md")
    text = path.read_text(encoding="utf-8")
    if DIRECTION_ID not in text:
        block = f"""

## {DIRECTION_ID}

direction_id: {DIRECTION_ID}
status: active
created_at: 2026-06-10
target_exp_ids:
  - {exp_id}

hypothesis:
  Simple ARC-style rules that exactly match official train examples and pass local validation can be batched so multiple independently plausible replacements receive leaderboard feedback within the daily submission cap.

leaderboard_basis:
  source_id: {LEADERBOARD_SOURCE_ID}
  reason: Competition discussion and agent-harness evidence support submitting validator-pass compact ONNX candidates for leaderboard feedback rather than relying only on cost proxy.

paper_basis:
  source_id: {PAPER_SOURCE_ID}
  reason: ARC Prize task-level reasoning supports exact rule synthesis from examples.

open_repo_basis:
  source_id: {OPEN_REPO_SOURCE_ID}
  reason: ARC-DSL primitives map directly to compact deterministic ONNX graph templates.

historical_competition_basis:
  source_id: {HISTORICAL_SOURCE_ID}
  reason: Prior ARC code-golf work supports task-wise exact solvers and batch ablation.

implementation_plan:
  - scan task001-task400 for simple exact train rules
  - generate locally validated ONNX replacements
  - submit conservative, medium, and aggressive multi-task batches
  - use binary ablation if a batch regresses

risk:
  - train-exact rules can still fail hidden cases
  - several individually plausible replacements may interact negatively in one batch

rollback_rule:
  Batch failures are split by binary ablation and only positive groups are retained.

success_criteria:
  At least one multi-task batch produces positive or neutral leaderboard feedback and records task-level ablation state.
"""
        path.write_text(text.rstrip() + block + "\n", encoding="utf-8")
        return
    if exp_id in text:
        return
    pattern = rf"(?ms)(## {re.escape(DIRECTION_ID)}.*?target_exp_ids:\s*\n)(?P<body>(?:\s{{2}}-[^\n]*\n?)*)"
    match = re.search(pattern, text)
    if not match:
        return
    insert_at = match.end("body")
    text = text[:insert_at] + f"  - {exp_id}\n" + text[insert_at:]
    path.write_text(text, encoding="utf-8")


def build_notebook(exp_id: str, candidate: Path) -> Path:
    notebook_path = root("notebooks/kaggle_submit_current.ipynb")
    build_submission_notebook(
        notebook_path,
        exp_id=exp_id,
        source_ids=[SOURCE_ID],
        dataset_slug="octaviograu/neurogolf-manual-rewrites-v205",
        source_subdir="submission",
        git_commit=git_commit(),
        embedded_zip_path=candidate / "submission.zip",
    )
    build_kernel_metadata(root("notebooks/kernel-metadata.json"), notebook_path.name, ["octaviograu/neurogolf-manual-rewrites-v205"])
    shutil.copy2(notebook_path, candidate / "notebook.ipynb")
    return candidate / "notebook.ipynb"


def write_batch_lists(exp_id: str, rows: list[dict]) -> None:
    path = root("task_bank", f"simple_exact_batch_{exp_id}.txt")
    path.write_text("\n".join(row["task_id"] for row in rows) + "\n", encoding="utf-8")
    if "080_simple_exact_batch_conservative" in exp_id:
        root("task_bank/simple_exact_batch_001.txt").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def update_batch_results(exp_id: str, rows: list[dict], status: str, score: str = "") -> None:
    path = root("task_bank/simple_exact_batch_results.csv")
    fields = [
        "exp_id",
        "created_at",
        "base_exp_id",
        "changed_task_count",
        "changed_tasks",
        "rule_names",
        "status",
        "submission_id",
        "public_score",
        "notes",
    ]
    _, existing = read_csv(path)
    existing = [row for row in existing if row.get("exp_id") != exp_id]
    manifest = root("submissions/candidates", exp_id, "manifest.json")
    base_exp_id = ""
    if manifest.exists():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        base_exp_id = payload.get("base_exp_id", "")
    existing.append(
        {
            "exp_id": exp_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "base_exp_id": base_exp_id,
            "changed_task_count": len(rows),
            "changed_tasks": ",".join(row["task_id"] for row in rows),
            "rule_names": ",".join(row["rule_name"] for row in rows),
            "status": status,
            "submission_id": "",
            "public_score": score,
            "notes": "built by simple exact multi-task replacement pipeline",
        }
    )
    write_csv(path, fields, existing)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-exp-id", required=True)
    parser.add_argument("--task-list", default="")
    parser.add_argument("--exp-id", required=True)
    parser.add_argument("--max-tasks", type=int, default=0)
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--smoke-examples-per-split", type=int, default=1)
    args = parser.parse_args()

    base = resolve_candidate(args.base_exp_id)
    base_dir = base / "onnx" if (base / "onnx").exists() else base
    if not base_dir.exists():
        raise SystemExit(f"base ONNX dir not found: {base_dir}")

    ensure_direction(args.exp_id)
    selected = selected_bank_rows(args, base_dir)
    if not selected:
        raise SystemExit("no content-changing simple exact rows available for this batch")

    candidate = root("submissions/candidates", args.exp_id)
    target = candidate / "onnx"
    target.mkdir(parents=True, exist_ok=True)
    copy_onnx_files(base_dir, target)

    changed_rows: list[dict] = []
    for row in selected:
        task_id = row["task_id"]
        src = ROOT / row["candidate_onnx_path"]
        dst = target / f"{task_id}.onnx"
        shutil.copy2(src, dst)
        changed_rows.append(
            {
                "task_id": task_id,
                "model_path": str(src),
                "source_id": SOURCE_ID,
                "method_family": "simple_exact_batch_replacement",
                "rule_family": row["rule_family"],
                "rule_name": row["rule_name"],
                "risk": row["estimated_hidden_risk"],
                "cost_proxy": "",
                "source_basis": row["source_basis"],
                "exact_solve_evidence": row["local_validation_status"],
            }
        )

    changed_fields = [
        "task_id",
        "model_path",
        "source_id",
        "method_family",
        "rule_family",
        "rule_name",
        "risk",
        "cost_proxy",
        "source_basis",
        "exact_solve_evidence",
    ]
    write_csv(candidate / "changed_tasks.csv", changed_fields, changed_rows)
    write_batch_lists(args.exp_id, selected)

    validation = validate_submission_dir(
        target,
        root("data/raw/neurogolf-2026"),
        smoke_examples_per_split=args.smoke_examples_per_split,
    )
    write_validation(candidate / "local_validation.json", validation)
    package = pack_submission_dir(target, candidate / "submission.zip")

    rules = sorted({row["rule_name"] for row in selected})
    families = sorted({row["rule_family"] for row in selected})
    manifest = {
        "exp_id": args.exp_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base": rel(base),
        "base_exp_id": args.base_exp_id,
        "parent_exp_id": args.base_exp_id,
        "source_id": SOURCE_ID,
        "primary_source_id": SOURCE_ID,
        "direction_id": DIRECTION_ID,
        "leaderboard_source_id": LEADERBOARD_SOURCE_ID,
        "paper_source_id": PAPER_SOURCE_ID,
        "open_repo_source_id": OPEN_REPO_SOURCE_ID,
        "historical_competition_source_id": HISTORICAL_SOURCE_ID,
        "evidence_gate_status": "pending",
        "risk": "low" if all(row["estimated_hidden_risk"] == "low" for row in selected) else "medium",
        "changed_tasks": [row["task_id"] for row in selected],
        "changed_task_count": len(selected),
        "rule_family_list": families,
        "rule_name_list": rules,
        "source_basis": "simple exact train-rule bank generated from official task JSON",
        "exact_solve_evidence": [
            {
                "task_id": row["task_id"],
                "rule_name": row["rule_name"],
                "train_pass_rate": row["train_pass_rate"],
                "local_validation_status": row["local_validation_status"],
                "params": parse_params(row.get("notes", "")),
            }
            for row in selected
        ],
        "validation_ok": validation.get("ok_for_submission_queue", False),
        **package,
    }
    write_manifest(candidate / "manifest.json", manifest)

    source_lines = [
        f"# {args.exp_id} Source Trace",
        "",
        f"base_exp_id: {args.base_exp_id}",
        f"direction_id: {DIRECTION_ID}",
        f"primary_source_id: {SOURCE_ID}",
        "",
        "leaderboard_basis:",
        f"  source_id: {LEADERBOARD_SOURCE_ID}",
        "  reason: validator-pass simple exact replacements need leaderboard feedback in batches under the daily submission cap.",
        "",
        "open_repo_basis:",
        f"  source_id: {OPEN_REPO_SOURCE_ID}",
        "  reason: generated ONNX templates are direct ARC-DSL-style deterministic primitives.",
        "",
        "## Replacements",
        "",
        "| task_id | rule | family | evidence | model |",
        "|---|---|---|---|---|",
    ]
    for row in selected:
        source_lines.append(
            f"| {row['task_id']} | {row['rule_name']} | {row['rule_family']} | "
            f"{row['local_validation_status']} | {row['candidate_onnx_path']} |"
        )
    (candidate / "source_trace.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")
    (candidate / "risk.md").write_text(
        f"# Risk\n\nrisk: {manifest['risk']}\nreason: train-exact simple rules batched for leaderboard feedback; ablation plan required if score decreases.\n",
        encoding="utf-8",
    )
    notebook = build_notebook(args.exp_id, candidate)

    local_valid = str(validation.get("ok_for_submission_queue", False)).lower()
    status = "queued_for_submit" if validation.get("ok_for_submission_queue") else "failed_local_validation"
    changed_tasks = ",".join(row["task_id"] for row in selected)

    upsert_csv(
        root("experiments/experiments.csv"),
        EXPERIMENT_FIELDS,
        "exp_id",
        {
            "exp_id": args.exp_id,
            "date": date.today().isoformat(),
            "lane": "S_simple_exact_batch_replacement",
            "direction_id": DIRECTION_ID,
            "leaderboard_source_id": LEADERBOARD_SOURCE_ID,
            "paper_source_id": PAPER_SOURCE_ID,
            "open_repo_source_id": OPEN_REPO_SOURCE_ID,
            "historical_competition_source_id": HISTORICAL_SOURCE_ID,
            "source_id": SOURCE_ID,
            "goal": "submit simple exact multi-task replacement batch",
            "changed_tasks": changed_tasks,
            "method": "simple_exact_batch_replacement",
            "local_valid": local_valid,
            "status": status,
            "next_action": "submit_queue" if validation.get("ok_for_submission_queue") else "inspect_validation",
        },
    )
    upsert_csv(
        root("experiments/submission_queue.csv"),
        QUEUE_FIELDS,
        "exp_id",
        {
            "exp_id": args.exp_id,
            "candidate_path": str(candidate),
            "risk": manifest["risk"],
            "direction_id": DIRECTION_ID,
            "leaderboard_source_id": LEADERBOARD_SOURCE_ID,
            "paper_source_id": PAPER_SOURCE_ID,
            "open_repo_source_id": OPEN_REPO_SOURCE_ID,
            "historical_competition_source_id": HISTORICAL_SOURCE_ID,
            "source_id": SOURCE_ID,
            "evidence_gate_status": "pending",
            "duplicate_hash": "false",
            "aggressive_change_score": "",
            "aggressive_change_classification": "unscored",
            "aggressive_change_gate_status": "pending",
            "changed_tasks": changed_tasks,
            "local_valid": local_valid,
            "notebook_ready": "true",
            "submitted": "false",
            "status": status,
            "next_action": "submit_notebook_output" if validation.get("ok_for_submission_queue") else "inspect_validation",
        },
    )
    upsert_csv(
        root("experiments/notebook_queue.csv"),
        NOTEBOOK_QUEUE_FIELDS,
        "exp_id",
        {
            "exp_id": args.exp_id,
            "notebook_path": str(notebook),
            "dataset_path": "embedded_submission_zip",
            "output_expected": "submission.zip",
            "kernel_slug": "muelsyse111/neurogolf-submit-current",
            "kernel_status": "not_pushed",
            "output_verified": "false",
            "ready_for_submit": str(bool(notebook and validation.get("ok_for_submission_queue"))).lower(),
            "notes": "Notebook embeds simple exact batch candidate zip.",
        },
    )

    evidence_payload = validate_experiments(ROOT, exp_id=args.exp_id)
    update_submission_queue(ROOT, evidence_payload["results"])
    for result in evidence_payload["results"]:
        update_candidate_manifest(ROOT, result["exp_id"], result)
    write_gate_outputs(ROOT, validate_experiments(ROOT))

    if validation.get("ok_for_submission_queue") and evidence_payload["fail_count"] == 0:
        ags_payload = score_candidate(ROOT, args.exp_id)
        write_score_outputs(ROOT, ags_payload)

    append_block(
        root("reports/SUBMISSION_ATTEMPTS.md"),
        f"""## {args.exp_id}

created_at: {datetime.now().isoformat(timespec="seconds")}
submission_path: submissions/candidates/{args.exp_id}/submission.zip
notebook_path: {notebook}
base_exp_id: {args.base_exp_id}
changed_tasks: {changed_tasks}
changed_task_count: {len(selected)}
rule_names: {','.join(rules)}
source_basis: simple_exact_task_bank
local_validation: {'pass' if validation.get('ok_for_submission_queue') else 'fail'}
examples_checked: {validation.get('examples_checked', '')}
examples_failed: {validation.get('examples_failed', '')}
status: {status}
risk: {manifest['risk']}
notes: generated by simple exact multi-task replacement pipeline
""",
    )
    update_batch_results(args.exp_id, selected, status)
    print(candidate)
    print("changed_tasks", changed_tasks)
    print("changed_task_count", len(selected))
    print("validation_ok", validation.get("ok_for_submission_queue", False))


if __name__ == "__main__":
    main()
