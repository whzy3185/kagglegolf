from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.paths import root
from neurogolf.reports import append_block
from neurogolf.submission import pack_submission_dir, write_manifest
from neurogolf.validation import validate_submission_dir, write_validation


def latest_candidate() -> str:
    candidates = sorted([p for p in root("submissions/candidates").iterdir() if p.is_dir()])
    if not candidates:
        raise SystemExit("No candidate directory found. Run script 06 first.")
    return candidates[-1].name


def update_experiments(exp_id: str, ok: bool) -> None:
    path = root("experiments/experiments.csv")
    rows = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            if row["exp_id"] == exp_id:
                row["local_valid"] = str(ok).lower()
                row["status"] = "queued_for_notebook" if ok else "failed_local_validation"
                row["next_action"] = "build_kaggle_notebook" if ok else "inspect_failed_files"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", default="")
    parser.add_argument("--smoke-examples-per-split", type=int, default=1)
    args = parser.parse_args()

    exp_id = args.exp_id or latest_candidate()
    candidate = root("submissions/candidates", exp_id)
    onnx_dir = candidate / "onnx"
    validation = validate_submission_dir(
        onnx_dir,
        root("data/raw/neurogolf-2026"),
        smoke_examples_per_split=args.smoke_examples_per_split,
    )
    write_validation(candidate / "local_validation.json", validation)
    manifest = pack_submission_dir(onnx_dir, candidate / "submission.zip")
    manifest["exp_id"] = exp_id
    manifest["validation_ok"] = validation["ok_for_submission_queue"]
    write_manifest(candidate / "manifest.json", {**json.loads((candidate / "manifest.json").read_text()), **manifest})

    update_experiments(exp_id, validation["ok_for_submission_queue"])
    append_block(
        root("reports/SUBMISSION_ATTEMPTS.md"),
        f"""## {exp_id} package update

created_at: {datetime.now().isoformat(timespec="seconds")}
submission_path: submissions/candidates/{exp_id}/submission.zip
package_sha256: {manifest['sha256']}
file_count: {manifest['file_count']}
package_size: {manifest['size_bytes']}
local_validation: {'pass' if validation['ok_for_submission_queue'] else 'fail'}
examples_checked: {validation['examples_checked']}
examples_failed: {validation['examples_failed']}
status: {'queued_for_notebook' if validation['ok_for_submission_queue'] else 'failed_local_validation'}
""",
    )
    print(candidate / "submission.zip")
    print("validation_ok", validation["ok_for_submission_queue"])


if __name__ == "__main__":
    main()

