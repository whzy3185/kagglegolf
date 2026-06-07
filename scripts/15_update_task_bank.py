from __future__ import annotations

import argparse
import csv
import json

from _bootstrap import ROOT
from neurogolf.paths import root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", required=True)
    args = parser.parse_args()
    candidate = root("submissions/candidates", args.exp_id)
    manifest = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for p in sorted((candidate / "onnx").glob("task*.onnx")):
        rows.append(
            {
                "task_id": p.stem,
                "source_id": manifest.get("source_id", ""),
                "source_type": "candidate",
                "model_path": str(p),
                "notes": args.exp_id,
            }
        )
    path = root("task_bank/task_sources.csv")
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "source_id", "source_type", "model_path", "notes"])
        for row in rows:
            writer.writerow(row)
    print(f"appended {len(rows)} task source rows")


if __name__ == "__main__":
    main()

