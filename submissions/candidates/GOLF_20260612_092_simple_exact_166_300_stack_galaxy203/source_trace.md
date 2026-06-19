# GOLF_20260612_092_simple_exact_166_300_stack_galaxy203 Source Trace

base_exp_id: GOLF_20260609_081_stack_galaxy203
direction_id: DIR_20260610_001_simple_exact_batch_replacement
primary_source_id: SRC_ARC_DSL_GITHUB

leaderboard_basis:
  source_id: SRC_DISCUSSION_AGENT_HARNESS_6580
  reason: validator-pass simple exact replacements need leaderboard feedback in batches under the daily submission cap.

open_repo_basis:
  source_id: SRC_ARC_DSL_GITHUB
  reason: generated ONNX templates are direct ARC-DSL-style deterministic primitives.

## Replacements

| task_id | rule | family | evidence | model |
|---|---|---|---|---|
| task166 | fill_bounding_box | fill | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task166/simple_exact/fill_bounding_box/task166.onnx |
| task300 | largest_color_crop | object_crop | pass: examples_checked=267; examples_failed=0 | task_bank/tasks/task300/simple_exact/largest_color_crop/task300.onnx |
