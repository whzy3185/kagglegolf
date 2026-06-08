from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root
from neurogolf.reports import append_block


COMPETITION = "neurogolf-2026"
KAGGLE_OWNER = "muelsyse111"
BASE_DATASET = "octaviograu/neurogolf-manual-rewrites-v205"

SOURCE_DATASETS = {
    "SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029": [BASE_DATASET, "jsrdcht/neurogolf-6029-submission-bundle"],
    "SRC_KAGGLE_NOTEBOOK_BEICICC_6645": [BASE_DATASET, "beicicc/neurogolf-6645-39-open-submission-artifact"],
    "SRC_KAGGLE_NOTEBOOK_VYANKTESH_MULTI_SOURCE": [BASE_DATASET, "vyankteshdwivedi/neurogolf-multi-source-onnx-solver"],
}

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


def read_queue() -> list[dict]:
    path = root("experiments/submission_queue.csv")
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_queue(rows: list[dict]) -> None:
    path = root("experiments/submission_queue.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(QUEUE_FIELDS)
    if path.exists() and path.stat().st_size:
        with path.open(newline="", encoding="utf-8") as existing:
            current_fields = list(csv.DictReader(existing).fieldnames or [])
        fields = current_fields + [field for field in fields if field not in current_fields]
    for row in rows:
        fields.extend(field for field in row if field not in fields)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row.get(k, "") for k in fields} for row in rows)


def upsert_csv(path: Path, fields: list[str], key: str, row: dict) -> None:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in fields} for r in rows)


def exp_slug(exp_id: str) -> str:
    slug = exp_id.lower()
    slug = re.sub(r"^golf-\d{8}-", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return f"neurogolf-submit-{slug}"[:100].strip("-")


def parse_version(text: str) -> str:
    patterns = [
        r"[Kk]ernel version\s+(\d+)",
        r"[Vv]ersion\s+(\d+)",
        r"/versions/(\d+)",
        r"versionNumber[=:]\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""


def read_manifest(candidate: Path) -> dict:
    path = candidate / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def package_sha(candidate: Path) -> str:
    manifest = read_manifest(candidate)
    return str(manifest.get("sha256") or manifest.get("package_sha256") or "")


def resolve_candidate_path(candidate_path: str, exp_id: str) -> Path:
    candidate = Path(candidate_path)
    if candidate.exists():
        return candidate
    return root("submissions/candidates", exp_id)


def submitted_package_hashes(rows: list[dict], current_exp_id: str) -> set[str]:
    hashes: set[str] = set()
    for row in rows:
        if row.get("exp_id") == current_exp_id or str(row.get("submitted", "")).lower() != "true":
            continue
        candidate_path = row.get("candidate_path", "")
        if candidate_path:
            sha = package_sha(
                resolve_candidate_path(candidate_path, row.get("exp_id", ""))
            )
            if sha:
                hashes.add(sha)
    for manifest in root("submissions/submitted").glob("*/manifest.json"):
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        sha = str(payload.get("package_sha256") or payload.get("sha256") or "")
        if sha:
            hashes.add(sha)
    for manifest in root("submissions/best").glob("*/manifest.json"):
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        sha = str(payload.get("package_sha256") or payload.get("sha256") or "")
        if sha:
            hashes.add(sha)
    return hashes


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def artifact_exists(candidate: Path) -> bool:
    return (
        (candidate / "submission.zip").exists()
        or (candidate / "notebook.ipynb").exists()
        or (candidate / "kaggle_kernel" / "notebook.ipynb").exists()
    )


def hard_gate_reasons(row: dict) -> list[str]:
    exp_id = row.get("exp_id", "")
    candidate = resolve_candidate_path(row.get("candidate_path", ""), exp_id)
    reasons: list[str] = []
    if truthy(row.get("submitted")):
        reasons.append("already_submitted")
    if not truthy(row.get("local_valid")):
        reasons.append("local_validation_not_passed")
    if not truthy(row.get("notebook_ready")):
        reasons.append("notebook_not_ready")
    if str(row.get("evidence_gate_status", "")).strip().lower() != "pass":
        reasons.append("evidence_gate_not_passed")
    if str(row.get("aggressive_change_gate_status", "")).strip().lower() != "pass":
        reasons.append("aggressive_change_gate_not_passed")
    if not str(row.get("changed_tasks", "")).strip():
        reasons.append("empty_changed_tasks")
    if not artifact_exists(candidate):
        reasons.append("missing_artifact")
    status = str(row.get("status", "")).strip().lower()
    if status in {
        "failed_local_validation",
        "validation_fail",
        "evidence_gate_failed",
        "metadata_only",
        "missing_artifact",
        "hard_gate_blocked",
    }:
        reasons.append(f"blocked_status:{row.get('status')}")
    return reasons


def platform_rejection(text: str) -> bool:
    lowered = text.lower()
    return any(
        token in lowered
        for token in [
            "submission limit",
            "maximum number of submissions",
            "not allowed",
            "cannot submit",
            "competition has ended",
            "forbidden",
            "unauthorized",
            "invalid submission",
            "platform",
        ]
    )


def dataset_sources(row: dict, notebook: Path) -> list[str]:
    sources = list(SOURCE_DATASETS.get(row.get("source_id", ""), []))
    if notebook.exists():
        text = notebook.read_text(encoding="utf-8", errors="ignore")
        for slug in re.findall(r"['\"]([a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*)['\"]", text):
            if slug not in sources and not slug.startswith("src_"):
                sources.append(slug)
    return sources


def write_zip_copy_notebook(path: Path, exp_id: str, source_id: str, changed_tasks: str) -> None:
    code = f"""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

EXP_ID = {exp_id!r}
SOURCE_ID = {source_id!r}
CHANGED_TASKS = {changed_tasks!r}
WORK = Path('/kaggle/working')
OUT = WORK / 'submission.zip'

search_roots = [Path.cwd(), WORK, Path('/kaggle/input')]
source_zip = None
for root in search_roots:
    if root.exists():
        for path in root.rglob('submission_source.zip'):
            source_zip = path
            break
    if source_zip:
        break
if source_zip is None:
    raise FileNotFoundError('submission_source.zip was not available in kernel files or Kaggle input')

shutil.copy2(source_zip, OUT)
with zipfile.ZipFile(OUT) as zf:
    files = [name for name in zf.namelist() if name.endswith('.onnx')]
    if len(files) != 400:
        raise RuntimeError(f'Expected 400 ONNX files, found {{len(files)}}')

h = hashlib.sha256()
with OUT.open('rb') as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b''):
        h.update(chunk)

manifest = {{
    'exp_id': EXP_ID,
    'source_id': SOURCE_ID,
    'changed_tasks': CHANGED_TASKS,
    'source_zip': str(source_zip),
    'package_sha256': h.hexdigest(),
    'file_count': len(files),
    'package_size': OUT.stat().st_size,
}}
print(json.dumps(manifest, indent=2))
print('submission.zip is ready at', OUT)
"""
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"# NeuroGolf submit\\n", f"exp_id: `{exp_id}`\\n"],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in code.strip().splitlines()],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")


def write_kernel_dir(row: dict, candidate: Path, notebook: Path, kernel_slug: str | None = None, code_file: str = "notebook.ipynb") -> tuple[Path, str]:
    slug = exp_slug(row["exp_id"])
    kernel_slug = kernel_slug or f"{KAGGLE_OWNER}/{slug}"
    kernel_dir = candidate / "kaggle_kernel"
    if kernel_dir.exists():
        shutil.rmtree(kernel_dir)
    kernel_dir.mkdir(parents=True, exist_ok=True)
    source_zip = candidate / "submission.zip"
    shutil.copy2(notebook, kernel_dir / code_file)
    title = kernel_slug.split("/", 1)[1]
    meta = {
        "id": kernel_slug,
        "title": title,
        "code_file": code_file,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "competition_sources": [COMPETITION],
        "dataset_sources": [] if source_zip.exists() else dataset_sources(row, notebook),
        "model_sources": [],
    }
    (kernel_dir / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return kernel_dir, kernel_slug


def run_with_retries(args: list[str], *, cwd: Path, timeout: int, attempts: int = 3, delay_seconds: int = 8) -> subprocess.CompletedProcess[str]:
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, attempts + 1):
        try:
            result = run_kaggle(args, cwd=cwd, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            result = subprocess.CompletedProcess(["kaggle", *args], 124, stdout=f"TimeoutExpired: {exc}", stderr="")
        last = result
        text = result.stdout or ""
        transient = any(token in text.lower() for token in ["ssl", "eof", "timeout", "temporarily", "connection reset", "500"])
        if result.returncode == 0 or not transient or attempt == attempts:
            return result
        time.sleep(delay_seconds)
    assert last is not None
    return last


def write_manual(exp_id: str, candidate: Path, kernel_slug: str, message: str, reason: str) -> Path:
    manual = root("reports", f"MANUAL_SUBMIT_{exp_id}.md")
    manual.write_text(
        f"""# Manual Submit: {exp_id}

reason: {reason}

Candidate: `{candidate}`
Kernel: `{kernel_slug}`
Expected output: `submission.zip`

1. Open Kaggle Code kernel `{kernel_slug}`.
2. Confirm the latest successful output contains `submission.zip`.
3. Submit `submission.zip` to competition `{COMPETITION}`.
4. Use this submit message:

```text
{message}
```

5. Poll and record:

```bash
python scripts/20_poll_submission_results.py --exp-id {exp_id}
python scripts/09_query_submission_history.py
```
""",
        encoding="utf-8",
    )
    return manual


def submit_local_fallback(
    row: dict,
    *,
    candidate: Path,
    message: str,
    reason: str,
) -> dict:
    exp_id = row["exp_id"]
    submission_zip = candidate / "submission.zip"
    if not submission_zip.exists():
        manual = write_manual(
            exp_id,
            candidate,
            "",
            message,
            f"{reason}; local submission.zip is missing",
        )
        row["status"] = "manual_submit_required"
        row["next_action"] = str(manual)
        return row
    fallback_message = message.replace(
        "target7800 aggressive candidate",
        "fallback_local_zip_after_notebook_output_failure",
    )
    result = run_with_retries(
        [
            "competitions",
            "submit",
            COMPETITION,
            "-f",
            str(submission_zip),
            "-m",
            fallback_message,
        ],
        cwd=ROOT,
        timeout=300,
    )
    log = root("reports", f"LOCAL_FALLBACK_SUBMIT_{exp_id}.txt")
    log.write_text(result.stdout or "", encoding="utf-8")
    ref_match = re.search(r"(\d{6,})", result.stdout or "")
    if result.returncode == 0:
        row["submitted"] = "true"
        row["submission_id"] = (
            ref_match.group(1) if ref_match else row.get("submission_id", "")
        )
        row["status"] = "submitted_waiting_score"
        row["next_action"] = "poll_submission_results"
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: submitted_waiting_score
submit_path: local_zip_fallback
fallback_reason: {reason}
submission_id: {row.get('submission_id', '')}
notes: {(result.stdout or '').strip()[:1000]}
""",
        )
        return row
    failure_text = result.stdout or ""
    if platform_rejection(failure_text):
        row["status"] = "platform_rejected"
        row["next_action"] = "review_kaggle_platform_response"
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: platform_rejected
submit_path: local_zip_fallback
fallback_reason: {reason}
notes: {failure_text.strip()[:1000]}
""",
        )
        return row
    manual = write_manual(
        exp_id,
        candidate,
        "",
        message,
        f"{reason}; local zip submit also failed: {failure_text[:300]}",
    )
    row["status"] = "manual_submit_required"
    row["next_action"] = str(manual)
    return row


def append_attempt(exp_id: str, block: str) -> None:
    append_block(root("reports/SUBMISSION_ATTEMPTS.md"), f"## {exp_id} submit attempt\n\n{block}")


def update_notebook_queue(exp_id: str, notebook_path: Path, kernel_slug: str, status: str, ready: str, notes: str) -> None:
    upsert_csv(
        root("experiments/notebook_queue.csv"),
        NOTEBOOK_QUEUE_FIELDS,
        "exp_id",
        {
            "exp_id": exp_id,
            "notebook_path": str(notebook_path),
            "dataset_path": "candidate_kaggle_kernel",
            "output_expected": "submission.zip",
            "kernel_slug": kernel_slug,
            "kernel_status": status,
            "output_verified": "false",
            "ready_for_submit": ready,
            "notes": notes,
        },
    )


def push_kernel(kernel_dir: Path, exp_id: str, label: str) -> subprocess.CompletedProcess[str]:
    result = run_with_retries(["kernels", "push", "-p", str(kernel_dir)], cwd=ROOT, timeout=300)
    push_log = root("reports", f"KERNEL_PUSH_{exp_id}_{label}.txt")
    push_log.write_text(result.stdout or "", encoding="utf-8")
    # Preserve the legacy log path for scripts/reports that already point to it.
    if label == "primary":
        root("reports", f"KERNEL_PUSH_{exp_id}.txt").write_text(result.stdout or "", encoding="utf-8")
    return result


def verify_kernel_output(kernel_slug: str, candidate: Path, exp_id: str, attempts: int = 12, delay_seconds: int = 15) -> tuple[bool, str]:
    output_dir = candidate / "kaggle_output"
    output_log = root("reports", f"KERNEL_OUTPUT_{exp_id}.txt")
    last_text = ""
    for attempt in range(1, attempts + 1):
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        result = run_with_retries(
            ["kernels", "output", kernel_slug, "-p", str(output_dir), "-o", "--file-pattern", "submission.zip"],
            cwd=ROOT,
            timeout=180,
            attempts=2,
            delay_seconds=5,
        )
        last_text = result.stdout or ""
        output_log.write_text(last_text, encoding="utf-8")
        if (output_dir / "submission.zip").exists():
            return True, str(output_dir / "submission.zip")
        if result.returncode != 0 and "not found" not in last_text.lower():
            break
        time.sleep(delay_seconds)
    return False, last_text[:500]


def submit_candidate(row: dict, all_rows: list[dict]) -> dict:
    exp_id = row["exp_id"]
    candidate = resolve_candidate_path(row["candidate_path"], exp_id)
    row["candidate_path"] = str(candidate)
    notebook = candidate / "notebook.ipynb"
    changed_tasks = [item for item in row.get("changed_tasks", "").split(",") if item.strip()]
    sha = package_sha(candidate)
    message = (
        f"{exp_id} | target7800 aggressive candidate | source={row.get('source_id', '')} | "
        f"changed={row.get('changed_tasks', '')} | risk={row.get('risk', '')} | local=pass"
    )

    pre_gate_reasons = [
        reason
        for reason in hard_gate_reasons(row)
        if reason != "already_submitted"
    ]
    if pre_gate_reasons:
        row["status"] = "hard_gate_blocked"
        row["next_action"] = "fix_hard_gate: " + ", ".join(pre_gate_reasons)
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: hard_gate_blocked
hard_gate_reasons: {', '.join(pre_gate_reasons)}
notes: soft penalties are not submission blockers
""",
        )
        return row

    gate = subprocess.run(
        [sys.executable, "scripts/25_validate_evidence_gate.py", "--exp-id", exp_id],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    gate_log = root("reports", f"EVIDENCE_GATE_SUBMIT_{exp_id}.txt")
    gate_log.write_text(
        (gate.stdout or "") + (("\n" + gate.stderr) if gate.stderr else ""),
        encoding="utf-8",
    )
    if gate.returncode != 0:
        row["evidence_gate_status"] = "fail"
        row["status"] = "evidence_gate_failed"
        row["next_action"] = "fix_direction_evidence"
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: evidence_gate_failed
next_action: fix_direction_evidence
notes: {gate_log}
""",
        )
        return row
    row["evidence_gate_status"] = "pass"

    if not notebook.exists():
        if (candidate / "submission.zip").exists():
            return submit_local_fallback(
                row,
                candidate=candidate,
                message=message,
                reason="candidate notebook is missing but local submission.zip exists",
            )
        row["status"] = "missing_artifact"
        row["next_action"] = "build_notebook_or_submission_zip"
        return row
    if not changed_tasks:
        row["status"] = "empty_changed_tasks_rejected"
        row["next_action"] = "inspect_candidate"
        return row
    duplicate_hash = bool(sha and sha in submitted_package_hashes(all_rows, exp_id))
    row["duplicate_hash"] = str(duplicate_hash).lower()
    if duplicate_hash:
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: duplicate_hash_soft_penalty
package_sha256: {sha}
notes: duplicate hash is recorded but not a hard blocker under current user policy
""",
        )

    ags = subprocess.run(
        [sys.executable, "scripts/27_score_aggressive_change.py", "--exp-id", exp_id],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    ags_log = root("reports", f"AGGRESSIVE_CHANGE_SUBMIT_{exp_id}.txt")
    ags_log.write_text(
        (ags.stdout or "") + (("\n" + ags.stderr) if ags.stderr else ""),
        encoding="utf-8",
    )
    ags_manifest = root("data/manifests", f"aggressive_change_{exp_id}.json")
    if ags.returncode != 0 or not ags_manifest.exists():
        row["aggressive_change_gate_status"] = "fail"
        row["status"] = "aggressive_change_score_failed"
        row["next_action"] = "inspect_aggressive_change_score"
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: aggressive_change_score_failed
next_action: inspect_aggressive_change_score
notes: {ags_log}
""",
        )
        return row
    ags_payload = json.loads(ags_manifest.read_text(encoding="utf-8"))
    classification = str(ags_payload.get("classification", ""))
    row["aggressive_change_score"] = f"{float(ags_payload.get('ags', 0.0)):.6f}"
    row["aggressive_change_classification"] = classification
    row["aggressive_change_gate_status"] = (
        "pass" if ags_payload.get("submission_gate_pass") else "fail"
    )
    if row["aggressive_change_gate_status"] != "pass" or classification in {
        "metadata_only",
        "validation_fail",
        "evidence_gate_fail",
    }:
        reason = classification if classification else "aggressive_change_gate_not_passed"
        row["status"] = "aggressive_change_gate_failed"
        row["next_action"] = f"resolve_{reason}"
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: aggressive_change_gate_failed
classification: {classification}
AGS: {row['aggressive_change_score']}
next_action: {row['next_action']}
small_tuning_penalty: {row.get('small_tuning_penalty', '')}
positive_probe_required_for_broad_mix: {row.get('positive_probe_required_for_broad_mix', '')}
notes: soft penalties do not block; this candidate failed a hard AGS/classification gate
""",
        )
        return row
    if classification in {"manual_review", "exploratory_submit"}:
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: aggressive_policy_calibration_submit
classification: {classification}
AGS: {row['aggressive_change_score']}
risk: {row.get('risk', '')}
notes: calibration phase permits submission under aggressive user policy
""",
        )

    kernel_dir, kernel_slug = write_kernel_dir(row, candidate, notebook)
    push = push_kernel(kernel_dir, exp_id, "primary")
    version = parse_version(push.stdout or "")

    if push.returncode != 0:
        fallback_slug = f"{KAGGLE_OWNER}/neurogolf-submit-current"
        kernel_dir, kernel_slug = write_kernel_dir(
            row,
            candidate,
            notebook,
            kernel_slug=fallback_slug,
            code_file="kaggle_submit_current.ipynb",
        )
        fallback_push = push_kernel(kernel_dir, exp_id, "fallback_current")
        if fallback_push.returncode == 0:
            push = fallback_push
            version = parse_version(push.stdout or "")
        else:
            return submit_local_fallback(
                row,
                candidate=candidate,
                message=message,
                reason=(
                    "primary and fallback kernel push failed; "
                    f"primary={str(push.stdout or '')[:160]}; "
                    f"fallback={str(fallback_push.stdout or '')[:160]}"
                ),
            )

    status = run_with_retries(["kernels", "status", kernel_slug], cwd=ROOT, timeout=120, attempts=2)
    status_log = root("reports", f"KERNEL_STATUS_{exp_id}.txt")
    status_log.write_text(status.stdout or "", encoding="utf-8")
    version = version or parse_version(status.stdout or "")
    update_notebook_queue(exp_id, notebook, kernel_slug, "pushed", "true", f"version={version or 'unknown'}")

    if not version:
        manual = write_manual(exp_id, candidate, kernel_slug, message, "kernel version could not be parsed from push/status output")
        row["status"] = "manual_submit_required"
        row["next_action"] = str(manual)
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
kernel_slug: {kernel_slug}
kernel_dir: {kernel_dir}
package_sha256: {sha}
status: manual_submit_required
notes: pushed but version was not parsed; see {status_log}
""",
        )
        return row

    output_ok, output_note = verify_kernel_output(kernel_slug, candidate, exp_id)
    if not output_ok:
        fallback = submit_local_fallback(
            row,
            candidate=candidate,
            message=message,
            reason=f"kernel output did not contain submission.zip: {output_note}",
        )
        update_notebook_queue(
            exp_id,
            notebook,
            kernel_slug,
            "output_missing_local_fallback",
            "false",
            fallback.get("status", ""),
        )
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
kernel_slug: {kernel_slug}
kernel_version: {version}
kernel_dir: {kernel_dir}
package_sha256: {sha}
status: {fallback.get('status', '')}
notes: output verification failed; attempted local zip fallback
""",
        )
        return fallback

    update_notebook_queue(exp_id, notebook, kernel_slug, "output_verified", "true", output_note)

    submit = run_with_retries(
        [
            "competitions",
            "submit",
            COMPETITION,
            "-k",
            kernel_slug,
            "-v",
            version,
            "-f",
            "submission.zip",
            "-m",
            message,
        ],
        cwd=ROOT,
        timeout=300,
    )
    submit_log = root("reports", f"KERNEL_SUBMIT_{exp_id}.txt")
    submit_log.write_text(submit.stdout or "", encoding="utf-8")
    ref_match = re.search(r"(\d{6,})", submit.stdout or "")
    if submit.returncode == 0:
        row["submitted"] = "true"
        row["submission_id"] = ref_match.group(1) if ref_match else row.get("submission_id", "")
        row["status"] = "submitted_waiting_score"
        row["next_action"] = "poll_submission_results"
    else:
        failure_text = submit.stdout or ""
        if platform_rejection(failure_text):
            row["status"] = "platform_rejected"
            row["next_action"] = "review_kaggle_platform_response"
        else:
            manual = write_manual(exp_id, candidate, kernel_slug, message, f"kernel-output submit failed: {failure_text[:300]}")
            row["status"] = "manual_submit_required"
            row["next_action"] = str(manual)
    append_attempt(
        exp_id,
        f"""created_at: {datetime.now().isoformat(timespec="seconds")}
kernel_slug: {kernel_slug}
kernel_version: {version}
kernel_dir: {kernel_dir}
package_sha256: {sha}
submit_command: kaggle competitions submit {COMPETITION} -k {kernel_slug} -v {version} -f submission.zip
submission_id: {row.get('submission_id', '')}
status: {row['status']}
notes: {(submit.stdout or '').strip()[:1000]}
""",
    )
    return row


def queue_row(exp_id: str) -> dict:
    for row in read_queue():
        if row.get("exp_id") == exp_id:
            return row
    return {}


def terminal_status(status: str) -> bool:
    lowered = status.lower()
    return any(token in lowered for token in ["complete", "failed", "error", "cancelled", "canceled"])


def failed_status(status: str) -> bool:
    lowered = status.lower()
    return any(token in lowered for token in ["failed", "error", "cancelled", "canceled"])


def write_wait_report(exp_id: str, events: list[dict], final_row: dict, outcome: str) -> None:
    lines = [
        f"# Submission Wait: {exp_id}",
        "",
        f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"outcome: {outcome}",
        f"submission_id: {final_row.get('submission_id', '')}",
        f"status: {final_row.get('status', '')}",
        f"public_score: {final_row.get('public_score', '')}",
        "",
        "## Poll Events",
        "",
        "| checked_at | status | public_score | submission_id |",
        "|---|---|---:|---|",
    ]
    for event in events:
        lines.append(
            f"| {event.get('checked_at', '')} | {event.get('status', '')} | "
            f"{event.get('public_score', '')} | {event.get('submission_id', '')} |"
        )
    root("reports", f"SUBMISSION_WAIT_{exp_id}.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def post_complete_updates(exp_id: str) -> None:
    commands = [
        [sys.executable, "scripts/30_record_task_attribution.py", "--exp-id", exp_id],
        [sys.executable, "scripts/31_sync_high_risk_register.py"],
        [sys.executable, "scripts/09_query_submission_history.py"],
    ]
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        label = Path(command[1]).stem
        root("reports", f"POST_COMPLETE_{label}_{exp_id}.txt").write_text(
            (result.stdout or "") + (("\n" + result.stderr) if result.stderr else ""),
            encoding="utf-8",
        )


def poll_submission(exp_id: str) -> dict:
    poll = subprocess.run(
        [sys.executable, "scripts/20_poll_submission_results.py", "--exp-id", exp_id],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    root("reports", f"POLL_AFTER_SUBMIT_{exp_id}.txt").write_text(
        (poll.stdout or "") + (("\n" + poll.stderr) if poll.stderr else ""),
        encoding="utf-8",
    )
    return queue_row(exp_id)


def poll_until_terminal(exp_id: str, *, wait_complete: bool, poll_interval: int, poll_timeout: int) -> dict:
    start = time.time()
    events: list[dict] = []
    final_row = poll_submission(exp_id)
    while True:
        event = {
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "status": final_row.get("status", ""),
            "public_score": final_row.get("public_score", ""),
            "submission_id": final_row.get("submission_id", ""),
        }
        events.append(event)
        status = str(final_row.get("status", ""))
        has_score = bool(str(final_row.get("public_score", "")).strip())
        if terminal_status(status):
            outcome = "complete" if "complete" in status.lower() else "failed"
            write_wait_report(exp_id, events, final_row, outcome)
            if "complete" in status.lower() and has_score:
                post_complete_updates(exp_id)
            append_attempt(
                exp_id,
                f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: poll_terminal_{outcome}
submission_status: {status}
public_score: {final_row.get('public_score', '')}
submission_id: {final_row.get('submission_id', '')}
notes: see reports/SUBMISSION_WAIT_{exp_id}.md
""",
            )
            return final_row
        if failed_status(status):
            write_wait_report(exp_id, events, final_row, "failed")
            return final_row
        if not wait_complete:
            write_wait_report(exp_id, events, final_row, "polled_once")
            return final_row
        if time.time() - start >= poll_timeout:
            final_row["status"] = "pending_timeout"
            final_row["next_action"] = "poll_submission_results"
            rows = read_queue()
            for row in rows:
                if row.get("exp_id") == exp_id:
                    row.update(final_row)
                    break
            write_queue(rows)
            write_wait_report(exp_id, events, final_row, "pending_timeout")
            append_attempt(
                exp_id,
                f"""created_at: {datetime.now().isoformat(timespec="seconds")}
status: pending_timeout
poll_timeout_seconds: {poll_timeout}
last_submission_status: {status}
notes: see reports/SUBMISSION_WAIT_{exp_id}.md
""",
            )
            return final_row
        time.sleep(max(1, poll_interval))


def checkpoint_commit(submitted_count: int) -> None:
    subprocess.run(["git", "add", "."], cwd=ROOT, check=False)
    commit = subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"submit: checkpoint hard-gate eligible submissions {submitted_count}",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    root("reports", f"CHECKPOINT_COMMIT_{submitted_count}.txt").write_text(
        (commit.stdout or "") + (("\n" + commit.stderr) if commit.stderr else ""),
        encoding="utf-8",
    )
    if commit.returncode == 0:
        push = subprocess.run(
            ["git", "push"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        root("reports", f"CHECKPOINT_PUSH_{submitted_count}.txt").write_text(
            (push.stdout or "") + (("\n" + push.stderr) if push.stderr else ""),
            encoding="utf-8",
        )


def run_selector() -> None:
    selection = subprocess.run(
        [sys.executable, "scripts/28_select_next_submission.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if selection.returncode != 0:
        raise SystemExit(
            "automatic candidate selection failed:\n"
            + (selection.stdout or "")
            + (selection.stderr or "")
        )


def submit_order(rows: list[dict]) -> list[str]:
    eligible: list[dict] = []
    for row in rows:
        reasons = hard_gate_reasons(row)
        if reasons:
            continue
        eligible.append(row)
    def sort_key(row: dict) -> tuple[float, int, str]:
        score_text = str(row.get("selection_score", "")).strip()
        try:
            score = float(score_text)
        except ValueError:
            score = -1.0
        try:
            rank = int(str(row.get("selected_rank", "")).strip() or "999999")
        except ValueError:
            rank = 999999
        return (-score, rank, row.get("exp_id", ""))
    return [row.get("exp_id", "") for row in sorted(eligible, key=sort_key)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", default="")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--auto-select", action="store_true")
    parser.add_argument("--submit-all-eligible", action="store_true")
    parser.add_argument("--poll-after-submit", action="store_true")
    parser.add_argument("--wait-complete", action="store_true")
    parser.add_argument("--poll-interval", type=int, default=60)
    parser.add_argument("--poll-timeout", type=int, default=1800)
    args = parser.parse_args()

    selected_exp_id = args.exp_id
    if args.auto_select or args.submit_all_eligible:
        run_selector()
    if args.auto_select and not args.submit_all_eligible:
        selection_manifest = root("data/manifests/next_submission_selection.json")
        if not selection_manifest.exists():
            raise SystemExit("automatic candidate selection did not create its manifest")
        selected_exp_id = str(
            json.loads(selection_manifest.read_text(encoding="utf-8")).get(
                "selected_exp_id", ""
            )
        )
        if not selected_exp_id:
            print("submit_attempts=0")
            print("selection_status=no_eligible_candidate")
            return

    count = 0
    if args.submit_all_eligible:
        ordered_exp_ids = submit_order(read_queue())
    else:
        ordered_exp_ids = [row.get("exp_id", "") for row in read_queue()]
    for exp_id in ordered_exp_ids:
        if selected_exp_id and exp_id != selected_exp_id:
            continue
        rows = read_queue()
        index = next((idx for idx, item in enumerate(rows) if item.get("exp_id") == exp_id), None)
        if index is None:
            continue
        row = rows[index]
        if truthy(row.get("submitted")):
            if args.poll_after_submit or args.wait_complete:
                poll_until_terminal(
                    exp_id,
                    wait_complete=args.wait_complete,
                    poll_interval=args.poll_interval,
                    poll_timeout=args.poll_timeout,
                )
            continue
        if args.submit_all_eligible:
            reasons = hard_gate_reasons(row)
            if reasons:
                row["status"] = "hard_gate_blocked"
                row["next_action"] = "fix_hard_gate: " + ", ".join(reasons)
                rows[index] = row
                write_queue(rows)
                continue
        elif str(row.get("local_valid", "")).lower() != "true" or str(row.get("notebook_ready", "")).lower() != "true":
            continue
        rows[index] = submit_candidate(row, rows)
        submitted_status = rows[index].get("status", "")
        write_queue(rows)
        if args.poll_after_submit or args.wait_complete:
            final_row = poll_until_terminal(
                exp_id,
                wait_complete=args.wait_complete,
                poll_interval=args.poll_interval,
                poll_timeout=args.poll_timeout,
            )
            rows = read_queue()
            index = next((idx for idx, item in enumerate(rows) if item.get("exp_id") == exp_id), None)
            if index is not None:
                submitted_status = rows[index].get("status", final_row.get("status", submitted_status))
        count += 1
        if args.submit_all_eligible and count % 3 == 0:
            checkpoint_commit(count)
        if submitted_status == "platform_rejected":
            print(f"platform_rejected={exp_id}")
        if count >= args.limit:
            break
    print(f"submit_attempts={count}")


if __name__ == "__main__":
    main()
