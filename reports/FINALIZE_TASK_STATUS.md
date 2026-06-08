# Finalize Task Status

checked_at: 2026-06-08T21:24:05
status: partial
message: feat: add negative-feedback-aware probe selection

## git_status_before

returncode: 0

```text
M configs/aggressive_change_score.yaml
 M data/manifests/aggressive_change_GOLF_20260608_016_jonathan_task255_probe.json
 M data/manifests/evidence_gate_status.json
 M data/manifests/kaggle_submission_history.json
 M data/manifests/next_submission_selection.json
 M experiments/experiments.csv
 M experiments/notebook_queue.csv
 M experiments/submission_queue.csv
 M notebooks/kaggle_submit_current.ipynb
 M reports/AGGRESSIVE_CHANGE_GOLF_20260608_016_jonathan_task255_probe.md
 M reports/AGGRESSIVE_CHANGE_SCORE_STATUS.md
 M reports/CURRENT_STATE.md
 M reports/EVIDENCE_GATE_STATUS.md
 M reports/KAGGLE_SUBMISSION_HISTORY.md
 M reports/NEXT_SUBMISSION_SELECTION.md
 M reports/PROBE_CANDIDATE_BUILD.md
 M reports/SCORECARD.md
 M reports/SUBMISSION_ATTEMPTS.md
 M reports/SUBMISSION_HISTORY_LATEST.txt
 M reports/TASK_ATTRIBUTION.md
 M research/DIRECTION_REGISTRY.md
 M scripts/19_submit_queue.py
 M scripts/28_select_next_submission.py
 M scripts/29_build_probe_candidates.py
 M scripts/30_record_task_attribution.py
 M submissions/candidates/GOLF_20260608_016_jonathan_task255_probe/manifest.json
 M task_bank/aggressive_change_scores.csv
 M task_bank/task_candidate_pool.csv
 M task_bank/task_status.csv
?? data/manifests/aggressive_change_GOLF_20260608_017_jonathan_task286_probe.json
?? data/manifests/aggressive_change_GOLF_20260608_018_jonathan_task173_probe.json
?? data/manifests/aggressive_change_GOLF_20260608_019_jonathan_top5_mix_probe.json
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_017_jonathan_task286_probe.md
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_018_jonathan_task173_probe.md
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_019_jonathan_top5_mix_probe.md
?? reports/AGGRESSIVE_CHANGE_SUBMIT_GOLF_20260608_016_jonathan_task255_probe.txt
?? reports/AGGRESSIVE_STRUCTURAL_CANDIDATES.md
?? reports/EVIDENCE_GATE_SUBMIT_GOLF_20260608_016_jonathan_task255_probe.txt
?? reports/KERNEL_PUSH_GOLF_20260608_016_jonathan_task255_probe.txt
?? reports/KERNEL_PUSH_GOLF_20260608_016_jonathan_task255_probe_fallback_current.txt
?? reports/KERNEL_PUSH_GOLF_20260608_016_jonathan_task255_probe_primary.txt
?? reports/KNOWN_BAD_FAMILIES.md
?? reports/LOCAL_FALLBACK_SUBMIT_GOLF_20260608_016_jonathan_task255_probe.txt
?? reports/LOW_VALUE_TUNING_POLICY.md
?? scripts/33_build_aggressive_structural_candidates.py
?? scripts/99_finalize_task.py
?? submissions/candidates/GOLF_20260608_017_jonathan_task286_probe/
?? submissions/candidates/GOLF_20260608_018_jonathan_task173_probe/
?? submissions/candidates/GOLF_20260608_019_jonathan_top5_mix_probe/

```

## query_submission_history

returncode: 0

```text
E:\kagglegolf\reports\submissions_raw_20260608_212408.txt

```

## poll_submission_results

returncode: 0

```text
E:\kagglegolf\reports\submissions_raw_20260608_212412.txt
E:\kagglegolf\experiments\submission_queue.csv

```

## record_task_attribution

returncode: 0

```text
attributed_experiments=8
attribution_rows=10

```

## select_next_submission

returncode: 0

```text
eligible=3
selected=GOLF_20260608_018_jonathan_task173_probe

```

## git_status_after

returncode: 0

```text
M configs/aggressive_change_score.yaml
 M data/manifests/aggressive_change_GOLF_20260608_016_jonathan_task255_probe.json
 M data/manifests/evidence_gate_status.json
 M data/manifests/kaggle_submission_history.json
 M data/manifests/next_submission_selection.json
 M experiments/experiments.csv
 M experiments/notebook_queue.csv
 M experiments/submission_queue.csv
 M notebooks/kaggle_submit_current.ipynb
 M reports/AGGRESSIVE_CHANGE_GOLF_20260608_016_jonathan_task255_probe.md
 M reports/AGGRESSIVE_CHANGE_SCORE_STATUS.md
 M reports/CURRENT_STATE.md
 M reports/EVIDENCE_GATE_STATUS.md
 M reports/KAGGLE_SUBMISSION_HISTORY.md
 M reports/NEXT_SUBMISSION_SELECTION.md
 M reports/PROBE_CANDIDATE_BUILD.md
 M reports/SCORECARD.md
 M reports/SUBMISSION_ATTEMPTS.md
 M reports/SUBMISSION_HISTORY_LATEST.txt
 M reports/TASK_ATTRIBUTION.md
 M research/DIRECTION_REGISTRY.md
 M scripts/19_submit_queue.py
 M scripts/28_select_next_submission.py
 M scripts/29_build_probe_candidates.py
 M scripts/30_record_task_attribution.py
 M submissions/candidates/GOLF_20260608_016_jonathan_task255_probe/manifest.json
 M task_bank/aggressive_change_scores.csv
 M task_bank/task_candidate_pool.csv
 M task_bank/task_status.csv
 M task_bank/task_submission_delta.csv
?? data/manifests/aggressive_change_GOLF_20260608_017_jonathan_task286_probe.json
?? data/manifests/aggressive_change_GOLF_20260608_018_jonathan_task173_probe.json
?? data/manifests/aggressive_change_GOLF_20260608_019_jonathan_top5_mix_probe.json
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_017_jonathan_task286_probe.md
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_018_jonathan_task173_probe.md
?? reports/AGGRESSIVE_CHANGE_GOLF_20260608_019_jonathan_top5_mix_probe.md
?? reports/AGGRESSIVE_CHANGE_SUBMIT_GOLF_20260608_016_jonathan_task255_probe.txt
?? reports/AGGRESSIVE_STRUCTURAL_CANDIDATES.md
?? reports/EVIDENCE_GATE_SUBMIT_GOLF_20260608_016_jonathan_task255_probe.txt
?? reports/KERNEL_PUSH_GOLF_20260608_016_jonathan_task255_probe.txt
?? reports/KERNEL_PUSH_GOLF_20260608_016_jonathan_task255_probe_fallback_current.txt
?? reports/KERNEL_PUSH_GOLF_20260608_016_jonathan_task255_probe_primary.txt
?? reports/KNOWN_BAD_FAMILIES.md
?? reports/LOCAL_FALLBACK_SUBMIT_GOLF_20260608_016_jonathan_task255_probe.txt
?? reports/LOW_VALUE_TUNING_POLICY.md
?? scripts/33_build_aggressive_structural_candidates.py
?? scripts/99_finalize_task.py
?? submissions/candidates/GOLF_20260608_017_jonathan_task286_probe/
?? submissions/candidates/GOLF_20260608_018_jonathan_task173_probe/
?? submissions/candidates/GOLF_20260608_019_jonathan_top5_mix_probe/

```

## git_add

returncode: 0

```text

warning: in the working copy of 'configs/aggressive_change_score.yaml', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'scripts/19_submit_queue.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'scripts/28_select_next_submission.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'scripts/29_build_probe_candidates.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'scripts/30_record_task_attribution.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'reports/LOW_VALUE_TUNING_POLICY.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'scripts/33_build_aggressive_structural_candidates.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'scripts/99_finalize_task.py', LF will be replaced by CRLF the next time Git touches it
```
