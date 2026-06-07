from __future__ import annotations

from datetime import datetime

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root


def main() -> None:
    result = run_kaggle(["competitions", "submissions", "-c", "neurogolf-2026"], cwd=ROOT, timeout=90)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = root("reports", f"submissions_raw_{ts}.txt")
    out.write_text(result.stdout or "", encoding="utf-8")
    root("reports/SUBMISSION_HISTORY_LATEST.txt").write_text(result.stdout or "", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()

