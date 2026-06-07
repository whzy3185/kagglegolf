from __future__ import annotations

import csv
import json
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.data_io import task_paths
from neurogolf.paths import root
from neurogolf.task_bank import write_initial_bank


def dims(grid: list[list[int]]) -> str:
    return f"{len(grid)}x{len(grid[0])}" if grid and grid[0] else "empty"


def main() -> None:
    data_dir = root("data/raw/neurogolf-2026")
    rows = []
    for path in task_paths(data_dir):
        task = json.loads(path.read_text(encoding="utf-8"))
        pair_counts = {k: len(task.get(k, [])) for k in ["train", "test", "arc-gen"]}
        max_dim = 0
        for split in ["train", "test", "arc-gen"]:
            for pair in task.get(split, []):
                for side in ["input", "output"]:
                    g = pair[side]
                    max_dim = max(max_dim, len(g), len(g[0]) if g else 0)
        rows.append(
            {
                "task_id": path.stem,
                "train_pairs": pair_counts["train"],
                "test_pairs": pair_counts["test"],
                "arc_gen_pairs": pair_counts["arc-gen"],
                "total_pairs": sum(pair_counts.values()),
                "max_grid_dim": max_dim,
            }
        )
    out = root("data/manifests/task_inventory.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["task_id"])
        writer.writeheader()
        writer.writerows(rows)
    if not root("task_bank/best_by_task.csv").exists() or not root("task_bank/task_status.csv").exists():
        write_initial_bank(root("task_bank/best_by_task.csv"), root("task_bank/task_status.csv"))
    print(f"Wrote {len(rows)} tasks to {out}")


if __name__ == "__main__":
    main()

