from __future__ import annotations

import argparse

from _task_table import score_submission


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()
    _, summary = score_submission(args.input, args.candidate_id)
    print(f"candidate_id={args.candidate_id}")
    print(f"current_total_score={summary['current_total_score']:.6f}")
    print(f"pass={summary['pass_count']} fail={summary['fail_count']} missing={summary['missing_count']}")
    for warning in summary.get("warnings", []):
        print(f"warning: {warning}")


if __name__ == "__main__":
    main()
