from __future__ import annotations

from _bootstrap import ROOT
from neurogolf.paths import root


def main() -> None:
    prompt = """You are continuing the NeuroGolf 2026 project in whzy3185/kagglegolf.

Start by reading:
- reports/CURRENT_STATE.md
- reports/SESSION_REPORT.md
- reports/SUBMISSION_ATTEMPTS.md
- research/EVIDENCE_REGISTRY.md
- task_bank/best_by_task.csv

Next actions:
1. Submit or confirm Notebook output for GOLF_20260607_001_public_6154_repro.
2. Record public LB with scripts/10_record_lb_result.py.
3. Build GOLF_20260607_002_public_6029_diff by diffing 6154 vs 6029 task ONNX costs.
4. Start single-task override loop for the highest-value public bundle differences.
"""
    root("reports/NEXT_ACTIONS.md").write_text("# Next Actions\n\n" + prompt, encoding="utf-8")
    root("reports/NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")
    print(root("reports/NEXT_PROMPT.md"))


if __name__ == "__main__":
    main()
