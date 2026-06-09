# GOLF_20260609_057_arc_dsl_task310_least_color_crop

## Goal

Compile the ARC-DSL `leastcolor -> ofcolor -> subgrid` rule for task310
into a bounded `8x8` ONNX crop graph.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- primary source: SRC_ARC_DSL_GITHUB
- leaderboard source: SRC_DISCUSSION_AGENT_HARNESS_6580
- paper source: SRC_ARC_PRIZE_2024_REPORT
- historical source: SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP
- parent_exp_id: GOLF_20260609_056_arc_dsl_task384_scaled_object_crop

## Changes

- task changed: task310
- verified specialization: select the least frequent color present and crop its bounding box
- validation of specialization: 266/266 official and ARC-GEN examples
- ONNX structure: color counts, present-color mask, ArgMin, bounded row/column Gather, static Pad

## Local validation

- examples checked: 266
- examples failed: 0
- structural validation: pass
- official memory before: 25573
- official parameters before: 166
- official points before: 14.844237
- official memory after: 19602
- official parameters after: 43
- official points after: 15.114422
- expected delta: +0.270184

## Submission

- status: build pending

## Rollback / merge decision

Promote only after Kaggle confirms the expected single-task delta.
