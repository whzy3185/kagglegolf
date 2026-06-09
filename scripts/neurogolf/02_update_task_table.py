from __future__ import annotations

import argparse
from pathlib import Path

from _task_table import update_task_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--snapshot")
    args = parser.parse_args()
    summary = update_task_table(args.candidate_id, Path(args.snapshot) if args.snapshot else None)
    print(f"updated_candidate_id={args.candidate_id}")
    print(f"current_total_score={summary.get('current_total_score', 0):.6f}")


if __name__ == "__main__":
    main()
