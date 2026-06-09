# GOLF_20260609_060_arc_dsl_task057_single_object_hconcat

## Goal

Compile the ARC-DSL `objects -> first -> subgrid -> hconcat(self)` rule for
task057 using bounded small-tensor gathers.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- primary source: SRC_ARC_DSL_GITHUB
- leaderboard source: SRC_DISCUSSION_AGENT_HARNESS_6580
- paper source: SRC_ARC_PRIZE_2024_REPORT
- historical source: SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP
- parent_exp_id: GOLF_20260609_059_arc_dsl_task278_size_two_outbox

## Changes

- task changed: task057
- verified specialization: every official and ARC-GEN example contains one
  nonzero object with a 3x3 bounding box; output duplicates the crop to 3x6
- ONNX structure: foreground bbox start, 3-row Gather, repeated 6-column
  Gather, constant zero Pad to the fixed tensor contract

## Local validation

- examples checked: 265
- examples failed: 0
- structural validation: pass
- official memory before: 29284
- official parameters before: 20
- official points before: 14.714521
- official memory after: 15448
- official parameters after: 10
- official points after: 15.354118
- expected delta: +0.639597

## Submission

- status: build pending

## Rollback / merge decision

Promote only after Kaggle confirms the expected single-task delta.
