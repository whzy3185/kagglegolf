from __future__ import annotations

import argparse

from _bootstrap import ROOT
from neurogolf.aggressive_score import score_candidate, write_score_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", required=True)
    args = parser.parse_args()

    payload = score_candidate(ROOT, args.exp_id)
    write_score_outputs(ROOT, payload)
    print(f"exp_id={args.exp_id}")
    print(f"AGS={payload['ags']:.6f}")
    print(f"classification={payload['classification']}")
    print(f"submission_gate_pass={str(payload['submission_gate_pass']).lower()}")


if __name__ == "__main__":
    main()
