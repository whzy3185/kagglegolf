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
        ("sync_high_risk_register", [sys.executable, "scripts/31_sync_high_risk_register.py"]),
        ("select_next_submission", [sys.executable, "scripts/28_select_next_submission.py"]),
        ("git_status_after", ["git", "status", "--short"]),
    ]
    command_rows = []
    error_rows = []
    for label, command in commands:
        result = run(command)
        append_command(lines, label, result)
        command_rows.append((checked_at, label, " ".join(command), result.returncode))
        if result.returncode != 0:
            error_rows.append((checked_at, label, result.returncode, (result.stderr or result.stdout or "").strip()[:500]))

    report = root("reports/FINALIZE_TASK_STATUS.md")
    report.write_text("\n".join(lines), encoding="utf-8")

    runs_index = root("reports/RUNS_INDEX.md")
    previous_runs = runs_index.read_text(encoding="utf-8") if runs_index.exists() else "# Runs Index\n\n| checked_at | status | message |\n|---|---|---|\n"
    previous_runs += f"| {checked_at} | {args.status} | {args.message} |\n"
    runs_index.write_text(previous_runs, encoding="utf-8")

    command_history = root("reports/COMMAND_HISTORY.md")
    previous_commands = command_history.read_text(encoding="utf-8") if command_history.exists() else "# Command History\n\n| checked_at | label | command | returncode |\n|---|---|---|---:|\n"
    for row in command_rows:
        previous_commands += f"| {row[0]} | {row[1]} | `{row[2]}` | {row[3]} |\n"
    command_history.write_text(previous_commands, encoding="utf-8")

    error_index = root("reports/ERROR_INDEX.md")
    previous_errors = error_index.read_text(encoding="utf-8") if error_index.exists() else "# Error Index\n\n| checked_at | label | returncode | note |\n|---|---|---:|---|\n"
    if error_rows:
        for row in error_rows:
            note = row[3].replace("|", "\\|").replace("\n", " ")
            previous_errors += f"| {row[0]} | {row[1]} | {row[2]} | {note} |\n"
    error_index.write_text(previous_errors, encoding="utf-8")

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
