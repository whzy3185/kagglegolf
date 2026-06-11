from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.data_io import load_task
from neurogolf.paths import root
from neurogolf.simple_exact import (
    BANK_FIELDS,
    build_simple_rule_onnx,
    candidate_for_bank_row,
    detect_task_candidates,
    load_bank,
    norm_task_id,
    rel,
    row_from_candidate,
    task_candidate_path,
    validation_status,
    write_csv,
)


def upsert_bank_rows(updated_rows: list[dict]) -> None:
    existing = load_bank()
    by_key = {
        (row.get("task_id", ""), row.get("rule_name", "")): row
        for row in existing
    }
    for row in updated_rows:
        by_key[(row["task_id"], row["rule_name"])] = row
    rows = list(by_key.values())
    rows.sort(key=lambda row: (row["task_id"], row["rule_name"]))
    write_csv(root("task_bank/simple_exact_task_bank.csv"), BANK_FIELDS, rows)


def generate_one(task_id: str, rule_name: str, out_dir: str = "") -> dict:
    task_id = norm_task_id(task_id)
    task = load_task(task_id, root("data/raw/neurogolf-2026"))
    candidate = next(
        (item for item in detect_task_candidates(task_id, task) if item.rule_name == rule_name),
        None,
    )
    if candidate is None:
        raise SystemExit(f"{task_id} does not have train-exact rule {rule_name}")
    out_path = (
        (Path(out_dir) if out_dir else task_candidate_path(task_id, rule_name))
        / f"{task_id}.onnx"
        if out_dir
        else task_candidate_path(task_id, rule_name)
    )
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    build_simple_rule_onnx(candidate.rule_name, candidate.params, out_path)
    ok, status = validation_status(task_id, out_path)
    if not ok:
        raise SystemExit(f"{task_id} {rule_name} failed local validation: {status}")
    return row_from_candidate(candidate, out_path, status)


def auto_rows(limit: int) -> list[dict]:
    rows = [
        row
        for row in load_bank()
        if row.get("eligible_for_batch", "").lower() == "true"
        and row.get("train_pass_rate") == "1.0"
    ]
    seen: set[str] = set()
    selected: list[dict] = []
    for row in rows:
        task_id = row.get("task_id", "")
        if task_id in seen:
            continue
        seen.add(task_id)
        selected.append(row)
        if limit and len(selected) >= limit:
            break
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default="")
    parser.add_argument("--rule-name", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--auto-from-bank", action="store_true")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    generated: list[dict] = []
    failures: list[str] = []
    if args.auto_from_bank:
        for row in auto_rows(args.limit):
            try:
                candidate = candidate_for_bank_row(row)
                onnx_path = task_candidate_path(candidate.task_id, candidate.rule_name)
                build_simple_rule_onnx(candidate.rule_name, candidate.params, onnx_path)
                ok, status = validation_status(candidate.task_id, onnx_path)
                if not ok:
                    failures.append(f"{candidate.task_id} {candidate.rule_name}: {status}")
                    continue
                generated.append(row_from_candidate(candidate, onnx_path, status))
            except Exception as exc:
                failures.append(f"{row.get('task_id')} {row.get('rule_name')}: {type(exc).__name__}: {exc}")
    else:
        if not args.task_id or not args.rule_name:
            raise SystemExit("use --task-id/--rule-name or --auto-from-bank")
        generated.append(generate_one(args.task_id, args.rule_name, args.out_dir))

    if generated:
        upsert_bank_rows(generated)

    generated_csv = root("task_bank/simple_exact_generated_onnx.csv")
    fields = ["generated_at", *BANK_FIELDS]
    generated_rows: list[dict] = []
    if generated_csv.exists() and generated_csv.stat().st_size:
        with generated_csv.open(newline="", encoding="utf-8") as handle:
            generated_rows = list(csv.DictReader(handle))
    now = datetime.now().isoformat(timespec="seconds")
    for row in generated:
        generated_rows.append({"generated_at": now, **row})
    write_csv(generated_csv, fields, generated_rows)

    report_path = root("reports/SIMPLE_EXACT_TASK_BANK.md")
    existing = report_path.read_text(encoding="utf-8") if report_path.exists() else "# Simple Exact Task Bank\n"
    lines = [
        existing.rstrip(),
        "",
        "## Latest ONNX Generation",
        "",
        f"generated_at: {now}",
        f"generated_count: {len(generated)}",
        f"failure_count: {len(failures)}",
        "",
        "| task_id | rule | onnx | validation |",
        "|---|---|---|---|",
    ]
    for row in generated:
        lines.append(
            f"| {row['task_id']} | {row['rule_name']} | {row['candidate_onnx_path']} | "
            f"{row['local_validation_status']} |"
        )
    if not generated:
        lines.append("| none | none | none | none |")
    if failures:
        lines.extend(["", "### Generation Failures", ""])
        lines.extend(f"- {item}" for item in failures[:80])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "generated_at": now,
        "generated_count": len(generated),
        "failures": failures,
        "generated_csv": rel(generated_csv),
    }
    root("data/manifests/simple_exact_generated_onnx.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(f"generated_count={len(generated)}")
    print(f"failure_count={len(failures)}")


if __name__ == "__main__":
    main()
