from __future__ import annotations

import argparse
import csv
import json
import subprocess

from _bootstrap import ROOT
from neurogolf.paths import root


QUEUE_FIELDS = [
    "exp_id",
    "candidate_path",
    "risk",
    "source_id",
    "changed_tasks",
    "local_valid",
    "notebook_ready",
    "submitted",
    "submission_id",
    "public_score",
    "status",
    "next_action",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", default="")
    args = parser.parse_args()

    subprocess.run(["python", "scripts/09_query_submission_history.py"], cwd=str(ROOT), check=False)
    history_path = root("data/manifests/kaggle_submission_history.json")
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else {}
    rows_by_exp = {}
    for row in history.get("rows", []):
        desc = row.get("description", "")
        exp_id = desc.split("|", 1)[0].strip()
        if exp_id:
            rows_by_exp[exp_id] = row

    queue_path = root("experiments/submission_queue.csv")
    if not queue_path.exists():
        print("no submission queue")
        return
    with queue_path.open(newline="", encoding="utf-8") as f:
        queue = list(csv.DictReader(f))
    for row in queue:
        exp_id = row.get("exp_id", "")
        if args.exp_id and exp_id != args.exp_id:
            continue
        hist = rows_by_exp.get(exp_id)
        if hist:
            row["submitted"] = "true"
            row["submission_id"] = hist.get("ref", "")
            row["public_score"] = hist.get("publicScore", "")
            row["status"] = hist.get("status", "")
            row["next_action"] = "record_delta"
    with queue_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows({k: row.get(k, "") for k in QUEUE_FIELDS} for row in queue)
    print(queue_path)


if __name__ == "__main__":
    main()
