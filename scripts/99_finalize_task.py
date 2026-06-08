from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.paths import root


def run(command: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def append_command(lines: list[str], label: str, result: subprocess.CompletedProcess[str]) -> None:
    lines.extend(
        [
            f"## {label}",
            "",
            f"returncode: {result.returncode}",
            "",
            "```text",
            (result.stdout or "").strip(),
            (result.stderr or "").strip(),
            "```",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", default="partial")
    parser.add_argument("--message", default="finalize task")
    args = parser.parse_args()

    checked_at = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# Finalize Task Status",
        "",
        f"checked_at: {checked_at}",
        f"status: {args.status}",
        f"message: {args.message}",
        "",
    ]

    commands = [
        ("git_status_before", ["git", "status", "--short"]),
        ("query_submission_history", [sys.executable, "scripts/09_query_submission_history.py"]),
        ("poll_submission_results", [sys.executable, "scripts/20_poll_submission_results.py"]),
        ("record_task_attribution", [sys.executable, "scripts/30_record_task_attribution.py", "--all-completed"]),
        ("select_next_submission", [sys.executable, "scripts/28_select_next_submission.py"]),
        ("git_status_after", ["git", "status", "--short"]),
    ]
    for label, command in commands:
        append_command(lines, label, run(command))

    report = root("reports/FINALIZE_TASK_STATUS.md")
    report.write_text("\n".join(lines), encoding="utf-8")

    add_targets = [
        "configs",
        "scripts",
        "src",
        "reports",
        "experiments",
        "task_bank",
        "data/manifests",
        "research",
        "submissions/candidates",
        "submissions/high_risk",
    ]
    add_result = run(["git", "add", *add_targets])
    append_command(lines, "git_add", add_result)
    report.write_text("\n".join(lines), encoding="utf-8")
    run(["git", "add", str(report)])

    diff_result = run(["git", "diff", "--cached", "--quiet"])
    if diff_result.returncode == 0:
        print("finalize_commit=none")
        push_result = run(["git", "push"])
        print(push_result.stdout.strip())
        return

    commit_message = args.message if args.message.startswith(("feat:", "fix:", "submit:", "score:", "research:", "exp:")) else f"feat: {args.message}"
    commit_result = run(["git", "commit", "-m", commit_message])
    if commit_result.returncode != 0:
        raise SystemExit(commit_result.stderr or commit_result.stdout)

    push_result = run(["git", "push"])
    if push_result.returncode != 0:
        raise SystemExit(push_result.stderr or push_result.stdout)
    print("finalize_commit=done")


if __name__ == "__main__":
    main()
