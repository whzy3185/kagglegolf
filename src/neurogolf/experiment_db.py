from __future__ import annotations

import csv
from pathlib import Path


EXPERIMENT_FIELDS = [
    "exp_id",
    "date",
    "lane",
    "source_id",
    "goal",
    "changed_tasks",
    "method",
    "local_valid",
    "local_score",
    "lb_score",
    "delta_vs_best",
    "status",
    "rollback_reason",
    "next_action",
]


def ensure_csv(path: Path, fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fields).writeheader()


def append_row(path: Path, fields: list[str], row: dict) -> None:
    ensure_csv(path, fields)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writerow({k: row.get(k, "") for k in fields})

