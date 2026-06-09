from __future__ import annotations

import argparse

from _task_table import watch_and_refresh


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    watch_and_refresh(args.input, args.candidate_id, args.interval, args.once)
