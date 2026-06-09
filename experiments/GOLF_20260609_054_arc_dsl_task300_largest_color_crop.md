# GOLF_20260609_054_arc_dsl_task300_largest_color_crop

## Goal

Compile the ARC-DSL `objects -> argmax(size) -> subgrid` rule for task300
into a compact static-shape ONNX graph.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- primary source: SRC_ARC_DSL_GITHUB
- leaderboard source: SRC_DISCUSSION_AGENT_HARNESS_6580
- paper source: SRC_ARC_PRIZE_2024_REPORT
- historical source: SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP
- parent_exp_id: GOLF_20260609_052_arc_dsl_task249_hconcat_self

## Changes

- task changed: task300
- verified specialization: select the most frequent nonzero color and crop its bounding box
- validation of specialization: 267/267 official and ARC-GEN examples
- ONNX structure: color count, ArgMax selection, dynamic bounding coordinates, row Gather, column Gather

## Local validation

- examples checked: 267
- examples failed: 0
- structural validation: pass
- official memory before: 77438
- official parameters before: 108
- official points before: 13.741373
- official memory after: 41272
- official parameters after: 72
- official points after: 14.370317
- expected delta: +0.628944

## Submission

- status: build pending

## Rollback / merge decision

Promote only after Kaggle confirms the expected single-task delta.
