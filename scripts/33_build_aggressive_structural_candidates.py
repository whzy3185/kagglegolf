from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime

from _bootstrap import ROOT
from neurogolf.paths import root


TARGETS = [
    "GOLF_20260608_018_mirza_top5_structural_probe",
    "GOLF_20260608_019_biohack_top5_structural_probe",
    "GOLF_20260608_020_jonathan_top5_structural_probe",
    "GOLF_20260608_021_mirza_solver_replacement_mix",
    "GOLF_20260608_022_biohack_solver_replacement_mix",
    "GOLF_20260608_023_memory_surgery_high_tail",
    "GOLF_20260608_024_HR_scorer_boundary_memory",
]


def run_builder(*args: str) -> tuple[list[str], str]:
    result = subprocess.run(
        [sys.executable, "scripts/29_build_probe_candidates.py", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    text = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
    generated = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("GOLF_")
    ]
    if result.returncode != 0:
        raise SystemExit(text)
    return generated, text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    generated: list[str] = []
    logs: list[str] = []

    first_batch, first_log = run_builder("--auto", "--mode", "single-task", "--limit", str(args.limit))
    generated.extend(first_batch)
    logs.append(first_log)

    remaining = max(0, args.limit - len(generated))
    if remaining:
        second_batch, second_log = run_builder(
            "--auto",
            "--mode",
            "top-k-mix",
            "--top-k",
            "5",
            "--limit",
            str(remaining),
        )
        generated.extend(second_batch)
        logs.append(second_log)

    lines = [
        "# Aggressive Structural Candidates",
        "",
        f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"limit: {args.limit}",
        "",
        "## Strategy",
        "",
        "- Generate P0 high-score single-task probes first.",
        "- Generate top-k structural probes only after single-task slots are exhausted.",
        "- Do not generate 50+ task broad mixes without positive probe feedback.",
        "- Mirza/Biohack exact-baseline outputs are skipped by hash equality.",
        "",
        "## Target Names",
        "",
    ]
    lines.extend(f"- {target}" for target in TARGETS)
    lines.extend(["", "## Generated This Run", ""])
    lines.extend(f"- {exp_id}" for exp_id in generated)
    if not generated:
        lines.append("- none")
    lines.extend(["", "## Builder Logs", ""])
    for index, log in enumerate(logs, start=1):
        lines.append(f"### Pass {index}")
        lines.append("")
        lines.append("```text")
        lines.append(log.strip())
        lines.append("```")
        lines.append("")

    root("reports/AGGRESSIVE_STRUCTURAL_CANDIDATES.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(f"generated={len(generated)}")
    for exp_id in generated:
        print(exp_id)


if __name__ == "__main__":
    main()

