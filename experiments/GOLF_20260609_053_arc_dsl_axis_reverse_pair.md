# GOLF_20260609_053_arc_dsl_axis_reverse_pair

## Goal

Compile two ARC-DSL axis-reversal solvers into smaller dynamic-width/height
ONNX graphs.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- source_id: SRC_ARC_DSL_GITHUB
- parent_exp_id: GOLF_20260609_052_arc_dsl_task249_hconcat_self

## Changes

- task150 / ARC 67a3c6ac: reverse valid columns
- task155 / ARC 68b16354: reverse valid rows
- infer the valid axis length from zero-hot padding and perform one dynamic
  `Gather`; padded rows or columns remain unchanged

## Local validation

- task150: 266 checked, 0 failed
- task155: 266 checked, 0 failed
- official cost before: 1014 per task
- official cost after: 681 per task
- expected total delta: +0.796192

## Submission

- candidate path: submissions/candidates/GOLF_20260609_053_arc_dsl_axis_reverse_pair
- submitted: pending

## Result analysis

Pending Kaggle feedback.

## Rollback / merge decision

Keep if Kaggle confirms the combined cost gain.

## Next action

Build and gate the candidate, check experiment 052, then submit without waiting.
