from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
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


def read_queue() -> list[dict]:
    path = root("experiments/submission_queue.csv")
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_queue(rows: list[dict]) -> None:
    path = root("experiments/submission_queue.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows({k: row.get(k, "") for k in QUEUE_FIELDS} for row in rows)


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


def submitted_package_hashes(rows: list[dict], current_exp_id: str) -> set[str]:
    hashes: set[str] = set()
    for row in rows:
        if row.get("exp_id") == current_exp_id or str(row.get("submitted", "")).lower() != "true":
            continue
        candidate_path = row.get("candidate_path", "")
        if candidate_path:
            sha = package_sha(Path(candidate_path))
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
    if source_zip.exists():
        shutil.copy2(source_zip, kernel_dir / "submission_source.zip")
        write_zip_copy_notebook(kernel_dir / code_file, row["exp_id"], row.get("source_id", ""), row.get("changed_tasks", ""))
    else:
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
    candidate = Path(row["candidate_path"])
    notebook = candidate / "notebook.ipynb"
    changed_tasks = [item for item in row.get("changed_tasks", "").split(",") if item.strip()]
    sha = package_sha(candidate)

    if not notebook.exists():
        row["status"] = "notebook_missing"
        row["next_action"] = "build_notebook"
        return row
    if not changed_tasks:
        row["status"] = "empty_changed_tasks_rejected"
        row["next_action"] = "inspect_candidate"
        return row
    if sha and sha in submitted_package_hashes(all_rows, exp_id):
        row["status"] = "duplicate_package_rejected"
        row["next_action"] = "build_distinct_candidate"
        return row

    kernel_dir, kernel_slug = write_kernel_dir(row, candidate, notebook)
    message = (
        f"{exp_id} | target7000 aggressive candidate | source={row.get('source_id', '')} | "
        f"changed={row.get('changed_tasks', '')} | risk={row.get('risk', '')} | local=pass"
    )

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
            manual = write_manual(
                exp_id,
                candidate,
                kernel_slug,
                message,
                f"kaggle kernels push failed; primary={str(push.stdout or '')[:160]}; fallback={str(fallback_push.stdout or '')[:160]}",
            )
            row["status"] = "manual_submit_required"
            row["next_action"] = str(manual)
            update_notebook_queue(exp_id, notebook, kernel_slug, "push_failed", "false", str(manual))
            append_attempt(
                exp_id,
                f"""created_at: {datetime.now().isoformat(timespec="seconds")}
kernel_slug: {kernel_slug}
kernel_dir: {kernel_dir}
package_sha256: {sha}
status: manual_submit_required
notes: primary and fallback kernel push failed
""",
            )
            return row

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
        manual = write_manual(exp_id, candidate, kernel_slug, message, f"kernel output did not contain submission.zip: {output_note}")
        row["status"] = "manual_submit_required"
        row["next_action"] = str(manual)
        update_notebook_queue(exp_id, notebook, kernel_slug, "output_missing", "false", str(manual))
        append_attempt(
            exp_id,
            f"""created_at: {datetime.now().isoformat(timespec="seconds")}
kernel_slug: {kernel_slug}
kernel_version: {version}
kernel_dir: {kernel_dir}
package_sha256: {sha}
status: manual_submit_required
notes: output verification failed before competition submit
""",
        )
        return row

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
        manual = write_manual(exp_id, candidate, kernel_slug, message, f"kernel-output submit failed: {str(submit.stdout or '')[:300]}")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", default="")
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()

    rows = read_queue()
    count = 0
    for i, row in enumerate(rows):
        if args.exp_id and row.get("exp_id") != args.exp_id:
            continue
        if row.get("submitted") == "true":
            continue
        if str(row.get("local_valid", "")).lower() != "true" or str(row.get("notebook_ready", "")).lower() != "true":
            continue
        rows[i] = submit_candidate(row, rows)
        count += 1
        if count >= args.limit:
            break
    write_queue(rows)
    print(f"submit_attempts={count}")


if __name__ == "__main__":
    main()
