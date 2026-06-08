# Submission Queue

Queue source: `experiments/submission_queue.csv`

Policy: every candidate with `local_valid=true` and `notebook_ready=true` is submitted. User policy treats submissions as unlimited; Kaggle platform rejection is recorded as `submit_failed` or `manual_submit_required`.

Current status:
- GOLF_20260607_002_public_6029_aggressive_mix: submitted via fallback local zip after Notebook-output path failed; submission 53472165; public 6154.59.
- GOLF_20260607_003_bottom15_single_task_probe: submitted via fallback local zip after Notebook-output path failed; submission 53472175; public 6154.67.
- GOLF_20260607_004_public_notebook_full_replace: blocked by local structural validation; do not submit original candidate.
