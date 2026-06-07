from __future__ import annotations

import json
import subprocess
from datetime import datetime

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root


EXP_ID = "GOLF_20260607_001_public_6154_repro"


def git_branch() -> str:
    result = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, text=True, stdout=subprocess.PIPE)
    return result.stdout.strip() or "unknown"


def main() -> None:
    candidate = root("submissions/candidates", EXP_ID)
    validation = {}
    manifest = {}
    if (candidate / "local_validation.json").exists():
        validation = json.loads((candidate / "local_validation.json").read_text(encoding="utf-8"))
    if (candidate / "manifest.json").exists():
        manifest = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
    lb = run_kaggle(["competitions", "leaderboard", "-c", "neurogolf-2026", "--show"], cwd=ROOT, timeout=90).stdout or ""
    submissions = run_kaggle(["competitions", "submissions", "-c", "neurogolf-2026"], cwd=ROOT, timeout=90).stdout or ""
    root("research/LEADERBOARD_INTEL.md").write_text(
        "# Leaderboard Intel\n\nCaptured: "
        + datetime.now().isoformat(timespec="seconds")
        + "\n\n```text\n"
        + lb[:6000]
        + "\n```\n",
        encoding="utf-8",
    )
    report = f"""# Session Report

Last updated: {datetime.now().isoformat(timespec="seconds")}

## Workspace

- Current directory: {ROOT}
- Current branch: {git_branch()}
- Competition: neurogolf-2026

## Data and Rules

- Official data manifest: data/manifests/official_files_manifest.json
- Task inventory: data/manifests/task_inventory.csv
- Rules summary: reports/RULES_SUMMARY.md

## Candidate

- exp_id: {EXP_ID}
- candidate path: submissions/candidates/{EXP_ID}
- submission path: submissions/candidates/{EXP_ID}/submission.zip
- notebook path: notebooks/kaggle_submit_current.ipynb
- source: {manifest.get('source_id', '')}
- package sha256: {manifest.get('sha256', '')}
- local validation ok: {validation.get('ok_for_submission_queue', '')}
- examples checked: {validation.get('examples_checked', '')}
- examples failed: {validation.get('examples_failed', '')}

## Kaggle Submission History

```text
{submissions[:2000]}
```

## Notes

Kaggle CLI can query data and leaderboard. Direct notebook-output submission is not exposed by the CLI, so the current candidate is prepared for manual notebook-output submission.
"""
    root("reports/SESSION_REPORT.md").write_text(report, encoding="utf-8")
    current = f"""# Current State

Current best LB:
Current best local score:
Current best submission path: submissions/candidates/{EXP_ID}/submission.zip
Current candidate in queue: {EXP_ID}
Current running Kaggle Notebook: notebooks/kaggle_submit_current.ipynb
Next candidate: GOLF_20260607_002_public_6029_diff
Known blockers: manual Kaggle Notebook output submit is required unless local zip upload is explicitly allowed
Last updated: {datetime.now().isoformat(timespec="seconds")}
"""
    root("reports/CURRENT_STATE.md").write_text(current, encoding="utf-8")
    print(root("reports/SESSION_REPORT.md"))


if __name__ == "__main__":
    main()

