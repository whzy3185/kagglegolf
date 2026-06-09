# GOLF_20260609_058_arc_dsl_task097_remove_isolated

## Goal

Compile the ARC-DSL `objects -> sizefilter(1) -> cover` rule for task097
into a local eight-neighbor graph.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- primary source: SRC_ARC_DSL_GITHUB
- leaderboard source: SRC_DISCUSSION_AGENT_HARNESS_6580
- paper source: SRC_ARC_PRIZE_2024_REPORT
- historical source: SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP
- parent_exp_id: GOLF_20260609_057_arc_dsl_task310_least_color_crop

## Changes

- task changed: task097
- verified specialization: replace isolated eight-neighbor foreground pixels with background
- validation of specialization: 267/267 official and ARC-GEN examples
- ONNX structure: foreground plane, 3x3 neighbor Conv, isolation mask, broadcast background Where

## Local validation

- examples checked: 267
- examples failed: 0
- structural validation: pass
- official memory before: 55802
- official parameters before: 10
- official points before: 14.070256
- official memory after: 18000
- official parameters after: 21
- official points after: 15.200707
- expected delta: +1.130451

## Submission

- status: complete
- submission id: 53497706
- public score: 6289.17
- delta vs parent: +1.13
- result: confirmed single-task win

## Rollback / merge decision

Promoted to the normal task bank after Kaggle confirmed the expected delta.
