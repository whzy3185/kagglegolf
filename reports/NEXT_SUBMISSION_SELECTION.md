# Next Submission Selection

checked_at: 2026-06-09T11:14:47
current_best: 6276.54 (GOLF_20260608_042_rogermt_task159_after020_probe)
candidate_count: 40
eligible_count: 3
blocked_count: 37
selected_candidate: GOLF_20260608_041_rogermt_task153_after020_probe
selection_score: 0.558097
selection_reason: class=operator_family_replacement; AGS=0.707; structural_scale=0.95; source=1.00; upside=0.85; novelty=0.60; attribution=1.00; tail_bonus=0.80; known_bad_penalty=0.00; small_tuning_penalty=0.00; recent_negative_source_penalty=1.00; same_family_negative_penalty=0.00; source_diversity_bonus=0.00; risk_penalty=0.35; source_negative=recent negative source feedback from GOLF_20260608_034_rogermt_6273_full_replace, GOLF_20260608_037_rogermt_task062_optimized_probe, GOLF_20260608_038_rogermt_task243_optimized_probe

policy: selection is ordering only, not a blocking gate
soft_penalties: affect submit order only; hard blocks are local validation, evidence gate, AGS gate, missing artifact, empty changed_tasks, already submitted, or explicit validation/evidence/metadata failure.

## Eligible Submit Order

| order | exp_id | score | soft_penalties |
|---:|---|---:|---|
| 1 | GOLF_20260608_041_rogermt_task153_after020_probe | 0.558097 | recent_negative_source_penalty |
| 2 | GOLF_20260608_044_rogermt_task092_after020_probe | 0.505065 | recent_negative_source_penalty |
| 3 | GOLF_20260608_039_rogermt_task255_after020_probe | 0.370844 | recent_negative_source_penalty, same_family_negative_penalty |

## Top 10

| rank | exp_id | score | class | risk | tasks | source |
|---:|---|---:|---|---|---:|---|
| 1 | GOLF_20260608_041_rogermt_task153_after020_probe | 0.558097 | operator_family_replacement | medium | 1 | SRC_HF_ROGERMT_6273_SUBMISSION |
| 2 | GOLF_20260608_044_rogermt_task092_after020_probe | 0.505065 | operator_family_replacement | medium | 1 | SRC_HF_ROGERMT_6273_SUBMISSION |
| 3 | GOLF_20260608_039_rogermt_task255_after020_probe | 0.370844 | operator_family_replacement | medium | 1 | SRC_HF_ROGERMT_6273_SUBMISSION |

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
- GOLF_20260608_040_rogermt_task128_after020_probe: already_submitted
- GOLF_20260608_042_rogermt_task159_after020_probe: already_submitted
- GOLF_20260608_043_rogermt_task208_after020_probe: already_submitted

## Negative Feedback Policy

Same-source, same-family, known-bad, low-upside, and broad-without-positive-probe signals reduce rank only. They do not block candidates that pass hard gates.

## Next Action

Submit all hard-gate eligible candidates through `scripts/19_submit_queue.py --submit-all-eligible --limit 999`.
