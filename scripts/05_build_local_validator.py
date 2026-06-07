from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT
from neurogolf.paths import root
from neurogolf.validation import validate_submission_dir, write_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission-dir", default="")
    parser.add_argument("--smoke-examples-per-split", type=int, default=0)
    parser.add_argument("--max-tasks", type=int, default=0)
    args = parser.parse_args()

    if args.submission_dir:
        payload = validate_submission_dir(
            root(args.submission_dir) if not args.submission_dir.startswith("/") else args.submission_dir,
            root("data/raw/neurogolf-2026"),
            smoke_examples_per_split=args.smoke_examples_per_split,
            max_tasks=args.max_tasks or None,
        )
    else:
        payload = {
            "status": "validator_ready",
            "usage": "python scripts/05_build_local_validator.py --submission-dir submissions/candidates/<exp_id>/onnx --smoke-examples-per-split 1",
        }
    out = root("reports/LOCAL_VALIDATOR.md")
    write_validation(out, payload)
    print(out)


if __name__ == "__main__":
    main()

