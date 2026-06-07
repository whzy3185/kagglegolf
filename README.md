# NeuroGolf 2026 ONNX Golf Workflow

Repository for the Kaggle competition `neurogolf-2026`.

The goal is not large-model training. The working loop is:

1. Extract the official data contract and validator behavior.
2. Build or import per-task ONNX solvers.
3. Validate structure and public examples locally.
4. Package `submission.zip`.
5. Generate a Kaggle Notebook that produces the same output.
6. Record provenance, leaderboard feedback, and rollback decisions.

## Quick Start

```bash
python scripts/00_bootstrap_repo.py
python scripts/01_check_kaggle.py
python scripts/02_download_competition_data.py
python scripts/03_extract_competition_spec.py
python scripts/04_build_task_inventory.py
python scripts/05_build_local_validator.py
python scripts/06_build_baseline_submission.py
python scripts/07_pack_submission.py
python scripts/08_build_kaggle_notebook.py
python scripts/17_make_session_report.py
python scripts/18_make_next_prompt.py
```

Kaggle credentials must remain outside the repository. Large competition data,
external bundles, ONNX intermediates, notebook outputs, and zip submissions are
ignored by Git.

## Current First-Round Baseline

The first candidate reproduces the public 6154.71 ONNX bundle from
`octaviograu/neurogolf-manual-rewrites-v205`, with the 6029.09 public all-task
bundle retained as fallback evidence.

The project intentionally keeps the first loop small: enough to validate,
package, and submit through Kaggle Notebook output, while leaving deeper
operator rewrites and single-task overrides for subsequent experiments.

