# GOLF_20260609_056_arc_dsl_task384_scaled_object_crop

## Goal

Compile the ARC-DSL `objects -> first -> subgrid -> upscale(2)` rule for
task384 into a bounded-memory static ONNX graph.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- primary source: SRC_ARC_DSL_GITHUB
- leaderboard source: SRC_DISCUSSION_AGENT_HARNESS_6580
- paper source: SRC_ARC_PRIZE_2024_REPORT
- historical source: SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP
- parent_exp_id: GOLF_20260609_055_arc_dsl_task242_zero_bbox_mirror_crop

## Changes

- task changed: task384
- verified specialization: crop the only nonzero object and upscale it by two
- validation of specialization: 266/266 official and ARC-GEN examples
- ONNX structure: nonzero mask, bbox coordinates, bounded row/column Gather, scale-index reuse, static Pad

## Local validation

- examples checked: 266
- examples failed: 0
- structural validation: pass
- official memory before: 74616
- official parameters before: 106
- official points before: 13.778470
- official memory after: 27956
- official parameters after: 70
- official points after: 14.759112
- expected delta: +0.980642

## Submission

- status: build pending

## Rollback / merge decision

Promote only after Kaggle confirms the expected single-task delta.
