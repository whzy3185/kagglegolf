from __future__ import annotations

import argparse

from _bootstrap import ROOT
from neurogolf.evidence_gate import (
    update_candidate_manifest,
    update_submission_queue,
    validate_experiments,
    write_gate_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", default="")
    parser.add_argument("--direction-id", default="")
    args = parser.parse_args()

    payload = validate_experiments(
        ROOT,
        exp_id=args.exp_id,
        direction_id=args.direction_id,
    )
    update_submission_queue(ROOT, payload["results"])
    for result in payload["results"]:
        update_candidate_manifest(ROOT, result["exp_id"], result)
        print(
            f"{result['exp_id']}: {result['status']}"
            + (f" ({'; '.join(result['reasons'])})" if result["reasons"] else "")
        )
    status_payload = (
        validate_experiments(ROOT)
        if args.exp_id or args.direction_id
        else payload
    )
    write_gate_outputs(ROOT, status_payload)
    if payload["fail_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
