# GOLF_20260610_084_simple_exact_batch_082_B6 Source Trace

base_exp_id: GOLF_20260609_078_stack_galaxy021
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
| task036 | largest_object_crop | object_crop | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task036/simple_exact/largest_object_crop/task036.onnx |
| task166 | fill_bounding_box | fill | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task166/simple_exact/fill_bounding_box/task166.onnx |
| task276 | color_replacement | color_map | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task276/simple_exact/color_replacement/task276.onnx |
| task300 | largest_color_crop | object_crop | pass: examples_checked=267; examples_failed=0 | task_bank/tasks/task300/simple_exact/largest_color_crop/task300.onnx |
| task309 | color_replacement | color_map | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task309/simple_exact/color_replacement/task309.onnx |
| task380 | rotate270 | rotation | pass: examples_checked=267; examples_failed=0 | task_bank/tasks/task380/simple_exact/rotate270/task380.onnx |
