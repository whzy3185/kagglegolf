from __future__ import annotations

from _bootstrap import ROOT
from neurogolf.paths import root


def main() -> None:
    text = """# Next Candidate Sketch

1. GOLF_20260607_002_public_6029_diff: diff 6154 vs 6029 task-level ONNX and locate cost regressions/gains.
2. GOLF_20260607_003_task_rewrite_low_cost: pick the largest-cost task in 6154 and attempt constant folding or hand rewrite.
3. GOLF_20260607_004_public_blend_absorb: pull Konbu/Biohack/Nadeem public bundles and test single-task overrides.
"""
    out = root("reports/NEXT_CANDIDATE_SKETCH.md")
    out.write_text(text, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
