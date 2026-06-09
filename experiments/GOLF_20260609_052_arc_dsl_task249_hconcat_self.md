# GOLF_20260609_052_arc_dsl_task249_hconcat_self

## Goal

Compile ARC-DSL solver `a416b8f3` into a compact ONNX graph for NeuroGolf
`task249`.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- source_id: SRC_ARC_DSL_GITHUB
- parent_exp_id: GOLF_20260609_051_arc_dsl_task303_frontier_fill

## Changes

- task changed: task249
- DSL rule: `hconcat(I, I)`
- ONNX rewrite: infer valid width from zero-hot padding, create dynamic
  modulo-based column indices, and gather the repeated grid in one output node

## Local validation

- full task examples: 265 checked, 0 failed
- structural validation: pass
- official cost before: 8998
- official cost after: 680
- official task points before: 15.895242
- official task points after: 18.477907
- expected delta: +2.582665

## Submission

- candidate path: submissions/candidates/GOLF_20260609_052_arc_dsl_task249_hconcat_self
- evidence gate: pending
- AGS: pending
- submitted: pending

## Result analysis

Pending Kaggle feedback.

## Rollback / merge decision

Keep only if Kaggle confirms the expected task-level gain.

## Next action

Build, validate, score, and submit the candidate.
