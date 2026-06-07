from __future__ import annotations

import argparse
import csv
from datetime import datetime

from _bootstrap import ROOT
from neurogolf.experiment_db import append_row
from neurogolf.paths import root
from neurogolf.reports import append_block


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", required=True)
    parser.add_argument("--submission-id", default="")
    parser.add_argument("--public-score", default="")
    parser.add_argument("--rank", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    append_row(
        root("experiments/score_events.csv"),
        ["exp_id", "created_at", "submission_id", "public_score", "rank", "notes"],
        {
            "exp_id": args.exp_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "submission_id": args.submission_id,
            "public_score": args.public_score,
            "rank": args.rank,
            "notes": args.notes,
        },
    )
    append_block(
        root("reports/SCORECARD.md"),
        f"""## {args.exp_id}

created_at: {datetime.now().isoformat(timespec="seconds")}
submission_id: {args.submission_id}
public_score: {args.public_score}
rank: {args.rank}
notes: {args.notes}
""",
    )
    print("Recorded score event")


if __name__ == "__main__":
    main()

