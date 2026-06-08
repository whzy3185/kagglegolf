# Submission Failure Review

updated_at: 2026-06-08T22:30:00

## Summary

No Kaggle platform rejection was observed in the latest submission batch. All hard-gate eligible candidates submitted through local zip fallback where the notebook-output route failed, and Kaggle returned `SubmissionStatus.COMPLETE`.

## Hard-Gate Blocked

| exp_id | reason | action |
|---|---|---|
| GOLF_20260607_004_public_notebook_full_replace | local validation failed; AGS gate failed; bad raw full-replace artifact | do not submit raw 004; only submit normalized or structural-pass derivatives |
| GOLF_20260608_008_jonathan_constraint_logic_mix | local validation failed; AGS gate failed; raw full-replace artifact invalid | do not submit raw 008; only submit targeted validated probes |

## Submit Path Failures With Successful Fallback

| exp_id | failed path | fallback | final status | public score |
|---|---|---|---|---:|
| GOLF_20260608_020_beicicc_task366_probe | kernel output did not expose `submission.zip` | local zip fallback | COMPLETE | 6143.61 |
| GOLF_20260608_023_beicicc_task076_probe | kernel output did not expose `submission.zip` | local zip fallback | COMPLETE | 6142.58 |
| GOLF_20260608_021_jsrdcht_memory_task255_probe | kernel output did not expose `submission.zip` | local zip fallback | COMPLETE | 6151.46 |
| GOLF_20260608_024_jsrdcht_memory_task285_probe | kernel output did not expose `submission.zip` | local zip fallback | COMPLETE | 6148.79 |
| GOLF_20260608_022_jonathan_task285_probe | primary and fallback kernel push returned 400 | local zip fallback | COMPLETE | 6142.81 |
| GOLF_20260608_018_jonathan_task173_probe | primary and fallback kernel push returned 400 | local zip fallback | COMPLETE | 6153.77 |
| GOLF_20260608_019_jonathan_top5_mix_probe | primary and fallback kernel push returned 400 | local zip fallback | COMPLETE | 6139.85 |
| GOLF_20260608_017_jonathan_task286_probe | primary and fallback kernel push returned 400 | local zip fallback | COMPLETE | 6153.76 |

## Score Feedback

All latest hard-gate eligible probes were negative against the current best `6154.71`. The closest were:

- `GOLF_20260608_018_jonathan_task173_probe`: 6153.77, delta -0.94
- `GOLF_20260608_017_jonathan_task286_probe`: 6153.76, delta -0.95
- `GOLF_20260608_021_jsrdcht_memory_task255_probe`: 6151.46, delta -3.25

## Policy

Soft penalties, known-bad family, source negative feedback, and low expected upside do not block submission when hard gates pass. They only affect ordering and post-submit attribution.
