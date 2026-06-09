# GOLF_20260609_059_arc_dsl_task278_size_two_outbox

## Goal

Compile the ARC-DSL `objects -> sizefilter(2) -> outbox -> fill(3)` rule for
task278 into a compact local graph.

## Source basis

- direction_id: DIR_20260608_003_memory_first_onnx_surgery
- primary source: SRC_ARC_DSL_GITHUB
- leaderboard source: SRC_DISCUSSION_AGENT_HARNESS_6580
- paper source: SRC_ARC_PRIZE_2024_REPORT
- historical source: SRC_GOOGLE_CODE_GOLF_2025_CGI_WRITEUP
- parent_exp_id: GOLF_20260609_058_arc_dsl_task097_remove_isolated

## Changes

- task changed: task278
- verified specialization: foreground pixels with an orthogonal neighbor form
  the generated two-cell objects; paint their bounded 8-neighbor outbox color 3
- ONNX structure: channel gather, orthogonal-neighbor Conv, object mask,
  3x3 dilation Conv, valid-grid mask, broadcast replacement

## Local validation

- examples checked: 265
- examples failed: 0
- structural validation: pass
- official memory before: 30132
- official parameters before: 362
- official points before: 14.674715
- official memory after: 25200
- official parameters after: 30
- official points after: 14.864211
- expected delta: +0.189496

## Submission

- status: complete
- submission id: 53498437
- public score: 6289.36
- delta vs parent: +0.19
- result: confirmed single-task win

## Rollback / merge decision

Promoted to the normal task bank after Kaggle confirmed the expected delta.
