# GOLF_20260609_055_arc_dsl_task242_zero_bbox_mirror_crop

## Goal

Compile the ARC-DSL `vmirror -> ofcolor(0) -> subgrid` rule for task242
into a compact static-shape ONNX graph.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- primary source: SRC_ARC_DSL_GITHUB
- leaderboard source: SRC_DISCUSSION_AGENT_HARNESS_6580
- paper source: SRC_ARC_PRIZE_2024_REPORT
- historical source: SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP
- parent_exp_id: GOLF_20260609_053_arc_dsl_axis_reverse_pair

## Changes

- task changed: task242
- verified specialization: crop the original zero-color coordinates from a left-right mirrored 16x16 input
- validation of specialization: 266/266 official and ARC-GEN examples
- ONNX structure: zero-plane Gather, row/column ArgMax, indexed row/column Gather, static Pad

## Local validation

- examples checked: 266
- examples failed: 0
- structural validation: pass
- official memory before: 20074
- official parameters before: 45
- official points before: 15.090580
- official memory after: 7864
- official parameters after: 7
- official points after: 16.029060
- expected delta: +0.938480

## Submission

- status: build pending

## Rollback / merge decision

Promote only after Kaggle confirms the expected single-task delta.
