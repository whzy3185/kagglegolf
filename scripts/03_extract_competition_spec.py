from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root


PAGES = ["data-description", "Evaluation", "Constraints", "rules", "Description", "Other Resources"]


def get_page(name: str) -> str:
    result = run_kaggle(["competitions", "pages", "neurogolf-2026", "--content", "--page-name", name], cwd=ROOT, timeout=90)
    return result.stdout or ""


def main() -> None:
    pages = {name: get_page(name) for name in PAGES}
    manifest_path = root("data/manifests/sample_submission_manifest.json")
    manifest_path.write_text(
        json.dumps(
            {
                "sample_submission_present": False,
                "note": "Competition data exposes taskNNN.json files and neurogolf_utils; no sample submission file was present in the official zip.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = f"""# Rules Summary

Last updated: {date.today().isoformat()}

## Official Files

- `neurogolf_utils/neurogolf_utils.py`
- `task001.json` through `task400.json`
- No official sample submission file was found in the downloaded zip.

## Task Format

Each task JSON has `train`, `test`, and `arc-gen` lists. Each pair has `input` and `output` grids.
Grid cells are integers 0 through 9. Official pages state grid sizes range from 1x1 to 30x30, while the official utility ignores examples larger than 30x30 during validation.

## Tensor Contract

- Input name: `input`
- Output name: `output`
- Shape: `[1, 10, 30, 30]`
- Encoding: one-hot color channels, zero-hot outside the original grid border.
- Dtype: float32, per official `neurogolf_utils.py`.
- Opset: 10, per official `neurogolf_utils.py`.
- IR version: 10, per official `neurogolf_utils.py`.

## Submission Package

Submit `submission.zip` containing at most one ONNX file per task:

```text
task001.onnx
task002.onnx
...
task400.onnx
```

## ONNX Constraints

- Statically defined tensor and parameter shapes are required.
- One input and one output are required by the official utility.
- File size limit per ONNX: 1.44 MB.
- Banned ops from current official utility/page: `Loop`, `Scan`, `NonZero`, `Unique`, `Script`, `Function`, `Compress`.
- Custom domains, functions, subgraphs, duplicate value_info names, name collisions, sequences, nonpositive dimensions, and unsafe tensor names are rejected by the official utility.

## Scoring

For each functionally correct task network:

```text
max(1, 25 - ln(cost))
cost = memory_footprint_bytes + parameter_count
```

MACs do not contribute under the current utility changelog.

## Public/Private Validation

Correctness is checked against ARC-AGI public training v1 task examples plus a small private benchmark suite to discourage overfitting.

## External Sources

The rules page permits public external data/tools/models when reasonably accessible and rule-compliant. Private leaks, hidden answer reconstruction, and untraceable sources are forbidden by project policy.

## Final Submission Rule

The formal rules page snapshot states five submissions per day and up to two final submissions for judging.

Current submission quota note:
Original rule snapshot says 5 submissions/day, but repo evidence source `SRC_DISCUSSION_SUBMISSION_LIMIT_REENABLED` records a host-note claim that the competition was reset to allow 100 submissions/day. That host-note claim is not visible in the official rules snapshot captured here. Current repo policy: treat the rules page as the formal contract and confirm the live submission quota from Kaggle UI or CLI-visible behavior before batch submissions.

## Raw Page Snapshots

Page snapshots are stored in `data/manifests/competition_pages.json`.
"""
    root("reports/RULES_SUMMARY.md").write_text(summary, encoding="utf-8")
    root("data/manifests/competition_pages.json").write_text(json.dumps(pages, indent=2), encoding="utf-8")

    cfg_path = root("configs/competition.yaml")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg.setdefault("score", {}).pop("current_best_lb", None)
    cfg["competition"]["rules_last_checked"] = date.today().isoformat()
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    print(root("reports/RULES_SUMMARY.md"))


if __name__ == "__main__":
    main()
