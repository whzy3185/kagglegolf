from __future__ import annotations

import csv
from pathlib import Path


BEST_BY_TASK_FIELDS = [
    "task_id",
    "best_model_path",
    "source_id",
    "method",
    "local_correct",
    "local_cost",
    "lb_delta_if_known",
    "last_changed_exp_id",
    "status",
    "notes",
]

TASK_STATUS_FIELDS = [
    "task_id",
    "has_solution",
    "best_score",
    "best_cost",
    "correct_on_official_examples",
    "correct_on_arcgen_samples",
    "source_id",
    "method_family",
    "model_path",
    "last_exp_id",
    "risk",
    "notes",
]


def write_initial_bank(best_path: Path, status_path: Path, task_count: int = 400) -> None:
    best_path.parent.mkdir(parents=True, exist_ok=True)
    with best_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BEST_BY_TASK_FIELDS)
        writer.writeheader()
        for i in range(1, task_count + 1):
            writer.writerow({"task_id": f"task{i:03d}", "status": "unknown"})
    with status_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TASK_STATUS_FIELDS)
        writer.writeheader()
        for i in range(1, task_count + 1):
            writer.writerow({"task_id": f"task{i:03d}", "has_solution": "false", "risk": "unknown"})

