# Simple Exact Task Bank

updated_at: 2026-06-11T22:43:52
official_task_count: 400
tasks_scanned: 400
simple_exact_candidates_found: 23
tasks_with_eligible_candidate: 21
train_pass_requirement: 1.0
local_validation_requirement: pass

## Family Counts

| rule_family | eligible_rows |
|---|---:|
| object_crop | 5 |
| fill | 3 |
| rotation | 3 |
| color_map | 2 |
| mirror | 2 |
| upscale | 2 |
| cleanup | 1 |
| color_canvas | 1 |
| concat | 1 |
| count | 1 |
| crop | 1 |
| split | 1 |

## Eligible Rows

| task_id | rule | family | risk | validation | onnx |
|---|---|---|---|---|---|
| task031 | crop_nonzero_bbox | crop | low | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task031/simple_exact/crop_nonzero_bbox/task031.onnx |
| task087 | rotate180 | rotation | low | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task087/simple_exact/rotate180/task087.onnx |
| task140 | rotate180 | rotation | low | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task140/simple_exact/rotate180/task140.onnx |
| task150 | horizontal_mirror | mirror | low | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task150/simple_exact/horizontal_mirror/task150.onnx |
| task155 | vertical_mirror | mirror | low | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task155/simple_exact/vertical_mirror/task155.onnx |
| task223 | upscale_x3 | upscale | low | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task223/simple_exact/upscale_x3/task223.onnx |
| task307 | upscale_x2 | upscale | low | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task307/simple_exact/upscale_x2/task307.onnx |
| task031 | largest_color_crop | object_crop | medium | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task031/simple_exact/largest_color_crop/task031.onnx |
| task031 | largest_object_crop | object_crop | medium | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task031/simple_exact/largest_object_crop/task031.onnx |
| task036 | largest_object_crop | object_crop | medium | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task036/simple_exact/largest_object_crop/task036.onnx |
| task067 | first_hsplit | split | medium | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task067/simple_exact/first_hsplit/task067.onnx |
| task070 | fill_bounding_box | fill | medium | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task070/simple_exact/fill_bounding_box/task070.onnx |
| task097 | remove_isolated_pixels | cleanup | medium | pass: examples_checked=267; examples_failed=0 | task_bank/tasks/task097/simple_exact/remove_isolated_pixels/task097.onnx |
| task129 | most_color_canvas | color_canvas | medium | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task129/simple_exact/most_color_canvas/task129.onnx |
| task166 | fill_bounding_box | fill | medium | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task166/simple_exact/fill_bounding_box/task166.onnx |
| task249 | hconcat_self | concat | medium | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task249/simple_exact/hconcat_self/task249.onnx |
| task276 | color_replacement | color_map | medium | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task276/simple_exact/color_replacement/task276.onnx |
| task300 | largest_color_crop | object_crop | medium | pass: examples_checked=267; examples_failed=0 | task_bank/tasks/task300/simple_exact/largest_color_crop/task300.onnx |
| task303 | frontier_fill | fill | medium | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task303/simple_exact/frontier_fill/task303.onnx |
| task309 | color_replacement | color_map | medium | pass: examples_checked=265; examples_failed=0 | task_bank/tasks/task309/simple_exact/color_replacement/task309.onnx |
| task310 | least_color_crop | object_crop | medium | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task310/simple_exact/least_color_crop/task310.onnx |
| task325 | connected_component_count | count | medium | pass: examples_checked=266; examples_failed=0 | task_bank/tasks/task325/simple_exact/connected_component_count/task325.onnx |
| task380 | rotate270 | rotation | medium | pass: examples_checked=267; examples_failed=0 | task_bank/tasks/task380/simple_exact/rotate270/task380.onnx |

## Scan Coverage

| status | task_count |
|---|---:|
| detected_but_rejected | 3 |
| eligible | 21 |
| no_simple_rule | 376 |

## Rejected Train-Exact Candidates

Rows below were not admitted to the bank because generation or local validation failed.

- task014 least_color_crop: fail: examples_checked=266; examples_failed=4; example_failures:4
- task036 least_color_crop: fail: examples_checked=265; examples_failed=83; example_failures:83
- task049 least_color_crop: fail: examples_checked=268; examples_failed=5; example_failures:5
- task263 largest_color_crop: fail: examples_checked=267; examples_failed=139; example_failures:139
- task276 fill_bounding_box: fail: examples_checked=266; examples_failed=34; example_failures:34
- task300 largest_object_crop: fail: examples_checked=267; examples_failed=12; example_failures:12

## Data Source

- Official JSON tasks are read from `data/raw/neurogolf-2026`.
- Generated ONNX files live under `task_bank/tasks/*/simple_exact/` and are ignored by Git via the global `*.onnx` rule.
- `submission (1).zip` is present locally and remains an untracked artifact for later source comparison; it is not copied into this bank.

## Latest ONNX Generation

generated_at: 2026-06-11T22:44:18
generated_count: 21
failure_count: 0

| task_id | rule | onnx | validation |
|---|---|---|---|
| task031 | crop_nonzero_bbox | task_bank/tasks/task031/simple_exact/crop_nonzero_bbox/task031.onnx | pass: examples_checked=266; examples_failed=0 |
| task087 | rotate180 | task_bank/tasks/task087/simple_exact/rotate180/task087.onnx | pass: examples_checked=266; examples_failed=0 |
| task140 | rotate180 | task_bank/tasks/task140/simple_exact/rotate180/task140.onnx | pass: examples_checked=265; examples_failed=0 |
| task150 | horizontal_mirror | task_bank/tasks/task150/simple_exact/horizontal_mirror/task150.onnx | pass: examples_checked=266; examples_failed=0 |
| task155 | vertical_mirror | task_bank/tasks/task155/simple_exact/vertical_mirror/task155.onnx | pass: examples_checked=266; examples_failed=0 |
| task223 | upscale_x3 | task_bank/tasks/task223/simple_exact/upscale_x3/task223.onnx | pass: examples_checked=265; examples_failed=0 |
| task307 | upscale_x2 | task_bank/tasks/task307/simple_exact/upscale_x2/task307.onnx | pass: examples_checked=266; examples_failed=0 |
| task036 | largest_object_crop | task_bank/tasks/task036/simple_exact/largest_object_crop/task036.onnx | pass: examples_checked=265; examples_failed=0 |
| task067 | first_hsplit | task_bank/tasks/task067/simple_exact/first_hsplit/task067.onnx | pass: examples_checked=266; examples_failed=0 |
| task070 | fill_bounding_box | task_bank/tasks/task070/simple_exact/fill_bounding_box/task070.onnx | pass: examples_checked=266; examples_failed=0 |
| task097 | remove_isolated_pixels | task_bank/tasks/task097/simple_exact/remove_isolated_pixels/task097.onnx | pass: examples_checked=267; examples_failed=0 |
| task129 | most_color_canvas | task_bank/tasks/task129/simple_exact/most_color_canvas/task129.onnx | pass: examples_checked=265; examples_failed=0 |
| task166 | fill_bounding_box | task_bank/tasks/task166/simple_exact/fill_bounding_box/task166.onnx | pass: examples_checked=266; examples_failed=0 |
| task249 | hconcat_self | task_bank/tasks/task249/simple_exact/hconcat_self/task249.onnx | pass: examples_checked=265; examples_failed=0 |
| task276 | color_replacement | task_bank/tasks/task276/simple_exact/color_replacement/task276.onnx | pass: examples_checked=266; examples_failed=0 |
| task300 | largest_color_crop | task_bank/tasks/task300/simple_exact/largest_color_crop/task300.onnx | pass: examples_checked=267; examples_failed=0 |
| task303 | frontier_fill | task_bank/tasks/task303/simple_exact/frontier_fill/task303.onnx | pass: examples_checked=265; examples_failed=0 |
| task309 | color_replacement | task_bank/tasks/task309/simple_exact/color_replacement/task309.onnx | pass: examples_checked=265; examples_failed=0 |
| task310 | least_color_crop | task_bank/tasks/task310/simple_exact/least_color_crop/task310.onnx | pass: examples_checked=266; examples_failed=0 |
| task325 | connected_component_count | task_bank/tasks/task325/simple_exact/connected_component_count/task325.onnx | pass: examples_checked=266; examples_failed=0 |
| task380 | rotate270 | task_bank/tasks/task380/simple_exact/rotate270/task380.onnx | pass: examples_checked=267; examples_failed=0 |
