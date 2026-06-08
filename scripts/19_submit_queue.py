from __future__ import annotations

import argparse
import csv
import re
import shutil
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root
from neurogolf.reports import append_block


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


def parse_version(text: str) -> str:
    patterns = [
        r"[Kk]ernel version\s+(\d+)",
        r"[Vv]ersion\s+(\d+)",
        r"/versions/(\d+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return ""


def submit_candidate(row: dict) -> dict:
    exp_id = row["exp_id"]
    candidate = Path(row["candidate_path"])
    notebook = candidate / "notebook.ipynb"
    if not notebook.exists():
        row["status"] = "notebook_missing"
        row["next_action"] = "build_notebook"
        return row

    shutil.copy2(notebook, root("notebooks/kaggle_submit_current.ipynb"))
    message = (
        f"{exp_id} | target7000 aggressive candidate | source={row.get('source_id', '')} | "
        f"changed={row.get('changed_tasks', '')} | risk={row.get('risk', '')} | local=pass"
    )
    push = run_kaggle(["kernels", "push", "-p", str(root("notebooks"))], cwd=ROOT, timeout=300)
    version = parse_version(push.stdout or "")
    push_log = root("reports", f"KERNEL_PUSH_{exp_id}.txt")
    push_log.write_text(push.stdout or "", encoding="utf-8")

    if not version:
        manual = root("reports", f"MANUAL_SUBMIT_{exp_id}.md")
        manual.write_text(
            f"""# Manual Submit: {exp_id}

Kaggle CLI push did not expose a kernel version.

Candidate: `{candidate}`
Notebook: `{notebook}`
Kernel: `muelsyse111/neurogolf-submit-current`
Expected output: `submission.zip`
Submit message:

```text
{message}
```
""",
            encoding="utf-8",
        )
        row["status"] = "manual_submit_required"
        row["next_action"] = str(manual)
        return row

    submit = run_kaggle(
        [
            "competitions",
            "submit",
            "neurogolf-2026",
            "-k",
            "muelsyse111/neurogolf-submit-current",
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
    row["submitted"] = "true" if submit.returncode == 0 else "false"
    row["submission_id"] = ref_match.group(1) if ref_match else row.get("submission_id", "")
    row["status"] = "submitted_waiting_score" if submit.returncode == 0 else "submit_failed"
    row["next_action"] = "poll_submission_results" if submit.returncode == 0 else str(submit_log)
    append_block(
        root("reports/SUBMISSION_ATTEMPTS.md"),
        f"""## {exp_id} submit attempt

created_at: {datetime.now().isoformat(timespec="seconds")}
kernel_version: {version}
submit_command: kaggle competitions submit neurogolf-2026 -k muelsyse111/neurogolf-submit-current -v {version} -f submission.zip
submission_id: {row.get('submission_id', '')}
status: {row['status']}
notes: {submit.stdout.strip()[:1000] if submit.stdout else ''}
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
        rows[i] = submit_candidate(row)
        count += 1
        if count >= args.limit:
            break
    write_queue(rows)
    print(f"submit_attempts={count}")


if __name__ == "__main__":
    main()
