from __future__ import annotations

import csv
import shutil
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.experiment_db import EXPERIMENT_FIELDS, ensure_csv
from neurogolf.paths import ensure_dirs, root, touch_gitkeep
from neurogolf.task_bank import BEST_BY_TASK_FIELDS, TASK_STATUS_FIELDS, write_initial_bank


def write_if_missing(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    touch_gitkeep()

    ensure_csv(root("experiments/experiments.csv"), EXPERIMENT_FIELDS)
    ensure_csv(
        root("experiments/candidates.csv"),
        ["exp_id", "candidate_name", "created_at", "submission_path", "status", "sha256", "notes"],
    )
    ensure_csv(
        root("experiments/score_events.csv"),
        ["exp_id", "created_at", "submission_id", "public_score", "rank", "notes"],
    )
    ensure_csv(
        root("experiments/rollback_log.csv"),
        ["exp_id", "created_at", "decision", "reason", "next_action"],
    )

    if not root("task_bank/best_by_task.csv").exists() or not root("task_bank/task_status.csv").exists():
        write_initial_bank(root("task_bank/best_by_task.csv"), root("task_bank/task_status.csv"))
    ensure_csv(
        root("task_bank/task_sources.csv"),
        ["task_id", "source_id", "source_type", "model_path", "notes"],
    )

    write_if_missing(
        root("research/EVIDENCE_REGISTRY.md"),
        "# Evidence Registry\n\nAll external sources used for candidates must be listed here.\n",
    )
    for rel, title in [
        ("research/LEADERBOARD_INTEL.md", "Leaderboard Intel"),
        ("research/DISCUSSION_NOTES.md", "Discussion Notes"),
        ("research/PUBLIC_NOTEBOOKS.md", "Public Notebooks"),
        ("research/PUBLIC_REPOS.md", "Public Repos"),
        ("research/PAPER_NOTES.md", "Paper Notes"),
        ("research/HISTORICAL_WRITEUPS.md", "Historical Writeups"),
        ("research/ONNX_OPT_PLAYBOOK.md", "ONNX Opt Playbook"),
        ("research/ARC_SYNTHESIS_PLAYBOOK.md", "ARC Synthesis Playbook"),
    ]:
        write_if_missing(root(rel), f"# {title}\n\nStatus: initialized.\n")

    write_if_missing(
        root("reports/CURRENT_STATE.md"),
        """# Current State

Current best LB:
Current best local score:
Current best submission path:
Current candidate in queue:
Current running Kaggle Notebook:
Next candidate:
Known blockers:
Last updated:
""",
    )
    for rel, title in [
        ("reports/SUBMISSION_ATTEMPTS.md", "Submission Attempts"),
        ("reports/SESSION_REPORT.md", "Session Report"),
        ("reports/SCORECARD.md", "Scorecard"),
        ("reports/NEXT_ACTIONS.md", "Next Actions"),
        ("reports/REPRODUCIBILITY.md", "Reproducibility"),
        ("reports/RULES_SUMMARY.md", "Rules Summary"),
    ]:
        write_if_missing(root(rel), f"# {title}\n\nStatus: initialized.\n")

    # Keep pulled public notebooks if they already exist, but never require them.
    print(f"Bootstrapped NeuroGolf workflow at {ROOT}")
    print("Directories, CSV registries, report stubs, and task bank stubs are ready.")


if __name__ == "__main__":
    main()

