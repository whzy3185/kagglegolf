from __future__ import annotations

import argparse
import csv
import hashlib
import re
import subprocess
import sys
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.paths import root


BASE_EXP_ID = "GOLF_20260607_001_public_6154_repro"
BASE_PATH = "submissions/candidates/GOLF_20260607_001_public_6154_repro"
DIRECTION_ID = "DIR_20260608_001_public_highscore_harvest"
PAPER_SOURCE = "SRC_ARC_PRIZE_2024_REPORT"
OPEN_REPO_SOURCE = "SRC_ARC_GEN_GITHUB"
HISTORICAL_SOURCE = "SRC_GOOGLE_CODE_GOLF_2025"

BOTTOM_TAIL = {
    "task158",
    "task233",
    "task173",
    "task054",
    "task025",
    "task285",
    "task366",
    "task133",
    "task286",
    "task255",
    "task349",
    "task018",
    "task187",
    "task145",
    "task243",
}

SOURCES = {
    "SRC_KAGGLE_NOTEBOOK_BIOHACK_SUPER_BLEND": {
        "csv": "task_bank/candidate_overrides_biohack_partial.csv",
        "slug": "biohack",
        "start": 14,
        "risk": "medium",
    },
    "SRC_KAGGLE_NOTEBOOK_MIRZA_BEST_SCORE": {
        "csv": "task_bank/candidate_overrides_mirza_partial.csv",
        "slug": "mirza",
        "start": 12,
        "risk": "medium",
    },
    "SRC_KAGGLE_NOTEBOOK_SEDDIK_SURGICAL_ONNX": {
        "csv": "task_bank/candidate_overrides_seddik_surgical_onnx.csv",
        "slug": "seddik_memory_surgery",
        "start": 19,
        "risk": "medium",
    },
    "SRC_KAGGLE_NOTEBOOK_BEICICC_6645": {
        "csv": "task_bank/candidate_overrides_beicicc_structural_pass.csv",
        "slug": "beicicc",
        "start": 20,
        "risk": "medium",
    },
    "SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029": {
        "csv": "task_bank/candidate_overrides_6029.csv",
        "slug": "jsrdcht_memory",
        "start": 21,
        "risk": "high",
    },
    "SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX": {
        "csv": "task_bank/candidate_overrides_jonathan_structural_pass.csv",
        "slug": "jonathan",
        "start": 16,
        "risk": "medium",
    },
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root(value)


def read_rows(source_id: str) -> list[dict]:
    config = SOURCES[source_id]
    csv_path = root(config["csv"])
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    base = root(BASE_PATH, "onnx")
    existing_pairs = queued_or_submitted_pairs()
    rejected = {
        (row.get("source_id", ""), row.get("task_id", ""))
        for row in read_csv(root("task_bank/task_submission_delta.csv"))
        if row.get("decision") in {
            "rejected_for_current_base",
            "negative_or_mixed",
        }
    }
    candidates: list[dict] = []
    for row in rows:
        if str(row.get("local_valid", "")).lower() not in {"true", "1", "yes"}:
            continue
        model = resolve(row.get("candidate_model_path", ""))
        baseline = base / f"{row.get('task_id', '')}.onnx"
        if not model.exists() or not baseline.exists():
            continue
        if digest(model) == digest(baseline):
            continue
        if (source_id, row.get("task_id", "")) in existing_pairs:
            continue
        if (source_id, row.get("task_id", "")) in rejected:
            continue
        memory_gain = baseline.stat().st_size - model.stat().st_size
        row["_memory_gain"] = memory_gain
        row["_priority"] = (
            (1_000_000_000 if row.get("task_id") in BOTTOM_TAIL else 0)
            + max(memory_gain, 0) * 100
            - max(-memory_gain, 0)
        )
        candidates.append(row)
    candidates.sort(
        key=lambda row: (-int(row["_priority"]), int(row.get("candidate_rank") or 999999))
    )
    return candidates


def read_csv(path: Path) -> list[dict]:
    if not path.exists() or not path.stat().st_size:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def queued_or_submitted_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for row in read_csv(root("experiments/submission_queue.csv")):
        source_id = row.get("source_id", "")
        tasks = [item.strip() for item in str(row.get("changed_tasks", "")).split(",") if item.strip()]
        if len(tasks) > 5:
            continue
        for task_id in tasks:
            task_id = task_id.strip()
            if source_id and task_id:
                pairs.add((source_id, task_id))
    return pairs


def next_exp_id(source_id: str, task_suffix: str) -> str:
    config = SOURCES[source_id]
    used_numbers = {
        int(match.group(1))
        for path in root("submissions/candidates").iterdir()
        if path.is_dir()
        for match in [re.match(r"^GOLF_\d{8}_(\d{3})_", path.name)]
        if match
    }
    number = int(config["start"])
    while number in used_numbers:
        number += 1
    return f"GOLF_20260608_{number:03d}_{config['slug']}_{task_suffix}_probe"


def ensure_direction_target(exp_id: str) -> None:
    path = root("research/DIRECTION_REGISTRY.md")
    text = path.read_text(encoding="utf-8")
    if re.search(rf"(?m)^\s{{2}}-\s*{re.escape(exp_id)}\s*$", text):
        return
    header = f"## {DIRECTION_ID}"
    start = text.index(header)
    targets = text.index("target_exp_ids:", start)
    position = text.find("\n\n", targets)
    text = text[:position] + f"\n  - {exp_id}" + text[position:]
    path.write_text(text, encoding="utf-8")


def write_override_csv(exp_id: str, rows: list[dict]) -> Path:
    path = root("data/interim/probe_candidates", f"{exp_id}.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id",
        "candidate_model_path",
        "source_id",
        "source_exp_id",
        "method_family",
        "memory_footprint",
        "parameter_count",
        "file_size",
        "cost_proxy",
        "utility_proxy",
        "local_valid",
        "risk",
        "candidate_rank",
        "recommended_action",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            payload = {field: row.get(field, "") for field in fields}
            payload["candidate_rank"] = index
            payload["recommended_action"] = "probe_first"
            writer.writerow(payload)
    return path


def build_candidate(source_id: str, rows: list[dict], mode: str) -> str:
    suffix = (
        rows[0]["task_id"]
        if mode == "single-task"
        else f"top{len(rows)}_mix"
    )
    exp_id = next_exp_id(source_id, suffix)
    ensure_direction_target(exp_id)
    override_csv = write_override_csv(exp_id, rows)
    risk = SOURCES[source_id]["risk"]
    command = [
        sys.executable,
        "scripts/13_single_task_override.py",
        "--exp-id",
        exp_id,
        "--base",
        BASE_PATH,
        "--override-csv",
        str(override_csv),
        "--top-k",
        str(len(rows)),
        "--source-id",
        source_id,
        "--direction-id",
        DIRECTION_ID,
        "--leaderboard-source-id",
        source_id,
        "--paper-source-id",
        PAPER_SOURCE,
        "--open-repo-source-id",
        OPEN_REPO_SOURCE,
        "--historical-competition-source-id",
        HISTORICAL_SOURCE,
        "--risk",
        risk,
        "--validate",
        "--pack",
        "--build-notebook",
        "--record",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    subprocess.run(
        [sys.executable, "scripts/27_score_aggressive_change.py", "--exp-id", exp_id],
        cwd=ROOT,
        check=True,
    )
    return exp_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", choices=sorted(SOURCES))
    parser.add_argument(
        "--mode", choices=["single-task", "top-k-mix"], default="single-task"
    )
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    if not args.auto and not args.source_id:
        raise SystemExit("provide --source-id or --auto")

    source_ids = list(SOURCES) if args.auto else [args.source_id]
    generated: list[str] = []
    skipped: list[str] = []
    candidates_by_source = {source_id: read_rows(source_id) for source_id in source_ids}
    for source_id, candidates in candidates_by_source.items():
        if not candidates:
            skipped.append(
                f"{source_id}: no model differs from current baseline or artifact missing"
            )

    if args.mode == "single-task":
        offset = 0
        while len(generated) < args.limit:
            made_progress = False
            for source_id in source_ids:
                candidates = candidates_by_source.get(source_id, [])
                if offset >= len(candidates):
                    continue
                generated.append(build_candidate(source_id, [candidates[offset]], args.mode))
                made_progress = True
                if len(generated) >= args.limit:
                    break
            if not made_progress:
                break
            offset += 1
    else:
        for source_id in source_ids:
            candidates = candidates_by_source.get(source_id, [])
            if not candidates:
                continue
            generated.append(
                build_candidate(source_id, candidates[: args.top_k], args.mode)
            )
            if len(generated) >= args.limit:
                break

    report = [
        "# Probe Candidate Build",
        "",
        f"mode: {args.mode}",
        f"generated_count: {len(generated)}",
        "",
        "## Generated",
        "",
    ]
    report.extend(f"- {exp_id}" for exp_id in generated)
    if not generated:
        report.append("- none")
    report.extend(["", "## Skipped", ""])
    report.extend(f"- {item}" for item in skipped)
    if not skipped:
        report.append("- none")
    report.append("")
    root("reports/PROBE_CANDIDATE_BUILD.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(f"generated={len(generated)}")
    for exp_id in generated:
        print(exp_id)


if __name__ == "__main__":
    main()
