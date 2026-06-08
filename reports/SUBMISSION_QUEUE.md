# Submission Queue

Queue source: `experiments/submission_queue.csv`

Policy: every candidate with `local_valid=true` and `notebook_ready=true` is submitted. User policy treats submissions as unlimited; Kaggle platform rejection is recorded as `submit_failed` or `manual_submit_required`.
