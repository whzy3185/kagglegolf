# GOLF_20260609_051_arc_dsl_task303_frontier_fill

## Goal

Compile the public ARC-DSL solution for ARC task `c1d99e64` into a compact
task-specific ONNX graph and replace NeuroGolf `task303`.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- source_id: SRC_ARC_DSL_GITHUB
- parent_exp_id: GOLF_20260609_050_arc_dsl_task070_bbox_fill

## Changes

- task changed: task303
- ARC mapping: c1d99e64
- DSL rule: find uniform rows and columns, then fill their cells with color 2
- ONNX rewrite: replace the previous convolution graph with channel-count
  reductions, frontier masks, and one `Where`

## Local validation

- full task examples: 265 checked, 0 failed
- submission validation: 1200 checked, 0 failed
- structural validation: pass
- official cost before: 80710
- official cost after: 9432
- official task points before: 13.701382
- official task points after: 15.848137
- expected delta: +2.146754

## Submission

- candidate path: submissions/candidates/GOLF_20260609_051_arc_dsl_task303_frontier_fill
- package sha256: dd3a369d9baf0f471f69457a6ac397c261bfef6265e0358fa96c647768d19e6d
- evidence gate: pass
- AGS: 0.828875
- AGS classification: aggressive
- submitted: yes
- submission id: 53495622
- Kaggle score: 6282.47

## Result analysis

Kaggle confirmed a `+2.14` public-score gain over the parent candidate. This
matches the official local cost prediction to leaderboard rounding.

## Rollback / merge decision

Keep and promote `task303` into the normal task bank.

## Next action

Compile the next short, high-loss ARC-DSL solver.
