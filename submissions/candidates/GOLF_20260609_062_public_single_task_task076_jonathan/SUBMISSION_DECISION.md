# GOLF_20260609_062_public_single_task_task076_jonathan

decision: submit_ready_after_local_validation
candidate_id: GOLF_20260609_062_public_single_task_task076_jonathan
base_exp_id: GOLF_20260609_061_arc_dsl_task325_component_count_diagonal
changed_tasks:
- task076

## Source

primary_source_id: SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX
public_onnx_path: data/kaggle_code_single_task/extracted_onnx/jonathanchan__ngc26-constraint-smart-logic-mix-blending/task076.onnx
source_type: public_single_task_onnx

## Local Validation

file_count: 400
missing_tasks: 0
changed_task_count: 1
changed_task_expected: task076
validator_status: pass
official_task_score_status: pass
examples_failed: 0

## Score Delta

base_local_total_score: 6290.690912
candidate_local_total_score: 6292.901673
local_delta_vs_base: 2.210761
task076_base_score: 12.292867258634116
task076_public_score: 14.503627688842322
task076_estimated_gain: 2.2107604302082056

## Package

submission_zip: submissions/candidates/GOLF_20260609_062_public_single_task_task076_jonathan/submission.zip
submission_zip_sha256: e0d57f4ee68020ae6b5c71206ea8fbe8706708431eb7da82492f69884d7eca5a
notebook_path: submissions/candidates/GOLF_20260609_062_public_single_task_task076_jonathan/notebook.ipynb

## Risk

risk: medium
notes:
- This is a verified local official-score improvement from public ONNX extraction.
- It is still only a public-source single-task probe; leaderboard feedback may differ from local task score.
- Previous Jonathan task233 probe had negative public feedback, so task076 should be treated as a separate single-task probe and not promoted to normal best_by_task until Kaggle score confirms.
