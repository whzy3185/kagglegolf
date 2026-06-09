# Next Submission Selection

checked_at: 2026-06-09T10:49:39
current_best: 6275.07 (GOLF_20260608_036_rogermt_task020_optimized_probe)
candidate_count: 34
eligible_count: 0
blocked_count: 34
selected_candidate: none
selection_score: 
selection_reason: No eligible candidate.

policy: selection is ordering only, not a blocking gate
soft_penalties: affect submit order only; hard blocks are local validation, evidence gate, AGS gate, missing artifact, empty changed_tasks, already submitted, or explicit validation/evidence/metadata failure.

## Eligible Submit Order

| order | exp_id | score | soft_penalties |
|---:|---|---:|---|
| - | none | - | - |

## Top 10

| rank | exp_id | score | class | risk | tasks | source |
|---:|---|---:|---|---|---:|---|
| - | none | - | - | - | - | - |

## Blocked Candidates

- GOLF_20260607_002_public_6029_aggressive_mix: already_submitted
- GOLF_20260607_003_bottom15_single_task_probe: already_submitted
- GOLF_20260607_004_public_notebook_full_replace: local_validation_not_passed, aggressive_change_gate_not_passed, blocked_status:failed_local_validation
- GOLF_20260608_004b_beicicc_structural_pass_mix: already_submitted, aggressive_change_gate_not_passed
- GOLF_20260608_008_jonathan_constraint_logic_mix: local_validation_not_passed, aggressive_change_gate_not_passed, blocked_status:failed_local_validation
- GOLF_20260608_008b_jonathan_structural_pass_mix: already_submitted, aggressive_change_gate_not_passed
- GOLF_20260608_005_mirza_structural_pass_mix: already_submitted, aggressive_change_gate_not_passed
- GOLF_20260608_006_biohack_super_blend_structural_pass_mix: already_submitted, aggressive_change_gate_not_passed
- GOLF_20260608_016_jonathan_task233_probe: already_submitted
- GOLF_20260608_016_jonathan_task255_probe: already_submitted
- GOLF_20260608_017_jonathan_task286_probe: already_submitted
- GOLF_20260608_018_jonathan_task173_probe: already_submitted
- GOLF_20260608_019_jonathan_top5_mix_probe: already_submitted
- GOLF_20260608_020_beicicc_task366_probe: already_submitted
- GOLF_20260608_021_jsrdcht_memory_task255_probe: already_submitted
- GOLF_20260608_022_jonathan_task285_probe: already_submitted
- GOLF_20260608_023_beicicc_task076_probe: already_submitted
- GOLF_20260608_024_jsrdcht_memory_task285_probe: already_submitted
- GOLF_20260608_025_kojimar_6272_full_replace: already_submitted
- GOLF_20260608_014_biohack_task187_probe: already_submitted
- GOLF_20260608_012_mirza_task187_probe: already_submitted
- GOLF_20260608_026_beicicc_task169_probe: already_submitted
- GOLF_20260608_027_jsrdcht_memory_task018_probe: already_submitted
- GOLF_20260608_028_jonathan_task025_probe: already_submitted
- GOLF_20260608_029_seddik_surgery_6272: already_submitted
- GOLF_20260608_030_beicicc_inline_full: local_validation_not_passed, aggressive_change_gate_not_passed, blocked_status:failed_local_validation
- GOLF_20260608_031_beicicc_inline_396_mix: already_submitted
- GOLF_20260608_032_biohack_best_blend_max_full: already_submitted
- GOLF_20260608_033_massimiliano_task258_groupconv_probe: aggressive_change_gate_not_passed
- GOLF_20260608_034_rogermt_6273_full_replace: already_submitted
- GOLF_20260608_035_rogermt_task255_optimized_probe: already_submitted
- GOLF_20260608_036_rogermt_task020_optimized_probe: already_submitted
- GOLF_20260608_037_rogermt_task062_optimized_probe: already_submitted
- GOLF_20260608_038_rogermt_task243_optimized_probe: already_submitted

## Negative Feedback Policy

Same-source, same-family, known-bad, low-upside, and broad-without-positive-probe signals reduce rank only. They do not block candidates that pass hard gates.

## Next Action

Generate a validator-pass probe candidate, score it with AGS, then rerun selection.
