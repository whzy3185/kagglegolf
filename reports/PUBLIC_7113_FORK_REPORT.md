# Public 7113 Fork Report

updated_at: 2026-06-19T13:25:01
source_notebook: https://www.kaggle.com/code/franksunp/starter-baseline-compact-onnx-artifact-vi
payload_fork_kernel: https://www.kaggle.com/code/muelsyse111/neurogolf-7113-franksunp-payload-submit
exp_id: GOLF_20260619_100_franksunp_7113_public_fork
submission_id: 53833153
status: SubmissionStatus.COMPLETE
public_score: 7113.63
previous_best_public_score: 7015.36
delta_vs_previous_best: 98.27
target_score: 7800.0
gap_to_target: 686.37

## Artifact Structure

| item | value |
|---|---:|
| output zip bytes | 567520 |
| output zip sha256 | 5e301b1146f70be7a28aab0bbd2c6546661606d67a358be9fe5ac55d7c8f22d6 |
| ONNX files in output | 400 |
| missing task files | 0 |
| A SajayR picks | 376 |
| B Kojimar picks | 24 |

## Notebook Structure

- The notebook has a setup cell, a packaging cell, and a display cell.
- It looks under `/kaggle/input` for an asset with `submission.zip` or `ab_audit_manifest.json`.
- It copies the scored `submission.zip` into `/kaggle/working/submission.zip`.
- It asserts exactly `task001.onnx` through `task400.onnx`.
- The source asset is not listable from this account, so a private payload wrapper was pushed for reproducibility.

## Submission

Direct submission of the public output completed with public score 7113.63. The raw zip and ONNX files remain ignored local artifacts and are not intended for Git tracking.
