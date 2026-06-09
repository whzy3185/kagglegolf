# Finalize Task Status

checked_at: 2026-06-09T10:03:17
status: partial
message: submitted rogermt 6273 full replacement

## git_status_before

returncode: 0

```text
M data/manifests/evidence_gate_status.json
 M data/manifests/kaggle_submission_history.json
 M data/manifests/next_submission_selection.json
 M experiments/experiments.csv
 M experiments/notebook_queue.csv
 M experiments/submission_queue.csv
 M notebooks/kaggle_submit_current.ipynb
 M reports/AGGRESSIVE_CHANGE_SCORE_STATUS.md
 M reports/CURRENT_STATE.md
 M reports/EVIDENCE_GATE_STATUS.md
 M reports/HIGH_RISK_REGISTER.md
 M reports/KAGGLE_SUBMISSION_HISTORY.md
 M reports/KNOWN_BAD_FAMILIES.md
 M reports/NEXT_SUBMISSION_SELECTION.md
 M reports/SCORECARD.md
 M reports/SUBMISSION_ATTEMPTS.md
 M reports/SUBMISSION_HISTORY_LATEST.txt
 M reports/SUBMIT_ELIGIBILITY.md
 M reports/TASK_ATTRIBUTION.md
 M research/DIRECTION_REGISTRY.md
 M research/EVIDENCE_REGISTRY.md
 M src/neurogolf/aggressive_score.py
 M task_bank/aggressive_change_scores.csv
 M task_bank/task_candidate_pool.csv
 M task_bank/task_status.csv
 M task_bank/task_submission_delta.csv
?? data/manifests/aggressive_change_GOLF_20260608_033_massimiliano_task258_groupconv_probe.json
?? data/manifests/aggressive_change_GOLF_20260608_034_rogermt_6273_full_replace.json
?? external/public_notebooks/massimilianoghiotto_convolution_series_part_4/
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_033_massimiliano_task258_groupconv_probe.md
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_034_rogermt_6273_full_replace.md
?? reports/AGGRESSIVE_CHANGE_SUBMIT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/EVIDENCE_GATE_SUBMIT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/HF_REPO_PROBE_20260609.txt
?? reports/HF_ROGERMT_SIBLINGS_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_6276_WIDE_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_7000_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_ARC_NANO_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_BLEND_MAX_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_CONV_SERIES_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_ROGERMT_20260609.txt
?? reports/KERNEL_OUTPUT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/KERNEL_OUTPUT_MASSIMILIANO_CONV_PART4.txt
?? reports/KERNEL_PUSH_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/KERNEL_PUSH_GOLF_20260608_034_rogermt_6273_full_replace_fallback_current.txt
?? reports/KERNEL_PUSH_GOLF_20260608_034_rogermt_6273_full_replace_primary.txt
?? reports/KERNEL_STATUS_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/KERNEL_SUBMIT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/POLL_AFTER_SUBMIT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/SUBMISSION_WAIT_GOLF_20260608_034_rogermt_6273_full_replace.md
?? submissions/candidates/GOLF_20260608_033_massimiliano_task258_groupconv_probe/
?? submissions/candidates/GOLF_20260608_034_rogermt_6273_full_replace/

```

## query_submission_history

returncode: 0

```text
E:\kagglegolf\reports\submissions_raw_20260609_100319.txt

```

## poll_submission_results

returncode: 0

```text
E:\kagglegolf\reports\submissions_raw_20260609_100323.txt
E:\kagglegolf\experiments\submission_queue.csv

```

## record_task_attribution

returncode: 0

```text
attributed_experiments=26
attribution_rows=32

```

## sync_high_risk_register

returncode: 0

```text
high_risk_candidates=5

```

## select_next_submission

returncode: 0

```text
eligible=0
selected=none

```

## git_status_after

returncode: 0

```text
M data/manifests/evidence_gate_status.json
 M data/manifests/kaggle_submission_history.json
 M data/manifests/next_submission_selection.json
 M experiments/experiments.csv
 M experiments/notebook_queue.csv
 M experiments/submission_queue.csv
 M notebooks/kaggle_submit_current.ipynb
 M reports/AGGRESSIVE_CHANGE_SCORE_STATUS.md
 M reports/CURRENT_STATE.md
 M reports/EVIDENCE_GATE_STATUS.md
 M reports/HIGH_RISK_REGISTER.md
 M reports/KAGGLE_SUBMISSION_HISTORY.md
 M reports/KNOWN_BAD_FAMILIES.md
 M reports/NEXT_SUBMISSION_SELECTION.md
 M reports/SCORECARD.md
 M reports/SUBMISSION_ATTEMPTS.md
 M reports/SUBMISSION_HISTORY_LATEST.txt
 M reports/SUBMIT_ELIGIBILITY.md
 M reports/TASK_ATTRIBUTION.md
 M research/DIRECTION_REGISTRY.md
 M research/EVIDENCE_REGISTRY.md
 M src/neurogolf/aggressive_score.py
 M submissions/high_risk/GOLF_20260607_002_public_6029_aggressive_mix/score.md
 M submissions/high_risk/GOLF_20260607_003_bottom15_single_task_probe/score.md
 M submissions/high_risk/GOLF_20260608_021_jsrdcht_memory_task255_probe/score.md
 M submissions/high_risk/GOLF_20260608_024_jsrdcht_memory_task285_probe/score.md
 M submissions/high_risk/GOLF_20260608_027_jsrdcht_memory_task018_probe/score.md
 M task_bank/aggressive_change_scores.csv
 M task_bank/high_risk_task_bank.csv
 M task_bank/task_candidate_pool.csv
 M task_bank/task_status.csv
 M task_bank/task_submission_delta.csv
?? data/manifests/aggressive_change_GOLF_20260608_033_massimiliano_task258_groupconv_probe.json
?? data/manifests/aggressive_change_GOLF_20260608_034_rogermt_6273_full_replace.json
?? external/public_notebooks/massimilianoghiotto_convolution_series_part_4/
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_033_massimiliano_task258_groupconv_probe.md
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_034_rogermt_6273_full_replace.md
?? reports/AGGRESSIVE_CHANGE_SUBMIT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/EVIDENCE_GATE_SUBMIT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/HF_REPO_PROBE_20260609.txt
?? reports/HF_ROGERMT_SIBLINGS_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_6276_WIDE_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_7000_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_ARC_NANO_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_BLEND_MAX_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_CONV_SERIES_20260609.txt
?? reports/KAGGLE_KERNEL_SEARCH_ROGERMT_20260609.txt
?? reports/KERNEL_OUTPUT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/KERNEL_OUTPUT_MASSIMILIANO_CONV_PART4.txt
?? reports/KERNEL_PUSH_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/KERNEL_PUSH_GOLF_20260608_034_rogermt_6273_full_replace_fallback_current.txt
?? reports/KERNEL_PUSH_GOLF_20260608_034_rogermt_6273_full_replace_primary.txt
?? reports/KERNEL_STATUS_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/KERNEL_SUBMIT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/POLL_AFTER_SUBMIT_GOLF_20260608_034_rogermt_6273_full_replace.txt
?? reports/SUBMISSION_WAIT_GOLF_20260608_034_rogermt_6273_full_replace.md
?? submissions/candidates/GOLF_20260608_033_massimiliano_task258_groupconv_probe/
?? submissions/candidates/GOLF_20260608_034_rogermt_6273_full_replace/

```

## git_add

returncode: 0

```text

warning: in the working copy of 'research/DIRECTION_REGISTRY.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'research/EVIDENCE_REGISTRY.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/neurogolf/aggressive_score.py', LF will be replaced by CRLF the next time Git touches it
```
