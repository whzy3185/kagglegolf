# Next Submission Selection

checked_at: 2026-06-08T22:04:43
current_best: 6154.71 (GOLF_20260608_006_biohack_super_blend_structural_pass_mix)
candidate_count: 18
eligible_count: 8
blocked_count: 10
selected_candidate: GOLF_20260608_020_beicicc_task366_probe
selection_score: 0.549732
selection_reason: class=operator_family_replacement; AGS=0.862; structural_scale=0.95; source=1.00; upside=0.10; novelty=0.60; attribution=1.00; tail_bonus=1.00; known_bad_penalty=0.00; small_tuning_penalty=0.00; recent_negative_source_penalty=0.70; same_family_negative_penalty=0.00; source_diversity_bonus=0.00; risk_penalty=0.35; source_negative=recent negative source feedback from GOLF_20260608_004b_beicicc_structural_pass_mix

policy: selection is ordering only, not a blocking gate
soft_penalties: affect submit order only; hard blocks are local validation, evidence gate, AGS gate, missing artifact, empty changed_tasks, already submitted, or explicit validation/evidence/metadata failure.

## Eligible Submit Order

| order | exp_id | score | soft_penalties |
|---:|---|---:|---|
| 1 | GOLF_20260608_020_beicicc_task366_probe | 0.549732 | low_expected_lb_upside, recent_negative_source_penalty |
| 2 | GOLF_20260608_023_beicicc_task076_probe | 0.546613 | low_expected_lb_upside, recent_negative_source_penalty |
| 3 | GOLF_20260608_021_jsrdcht_memory_task255_probe | 0.250344 | low_expected_lb_upside, low_selection_score, recent_negative_source_penalty, same_family_negative_penalty |
| 4 | GOLF_20260608_024_jsrdcht_memory_task285_probe | 0.244896 | low_expected_lb_upside, low_selection_score, recent_negative_source_penalty, same_family_negative_penalty |
| 5 | GOLF_20260608_022_jonathan_task285_probe | 0.227764 | low_expected_lb_upside, low_selection_score, recent_negative_source_penalty, same_family_negative_penalty |
| 6 | GOLF_20260608_018_jonathan_task173_probe | 0.197199 | low_expected_lb_upside, low_selection_score, recent_negative_source_penalty, same_family_negative_penalty |
| 7 | GOLF_20260608_019_jonathan_top5_mix_probe | 0.160829 | low_expected_lb_upside, low_selection_score, recent_negative_source_penalty, same_family_negative_penalty |
| 8 | GOLF_20260608_017_jonathan_task286_probe | 0.098260 | low_expected_lb_upside, low_selection_score, recent_negative_source_penalty, same_family_negative_penalty |

## Top 10

| rank | exp_id | score | class | risk | tasks | source |
|---:|---|---:|---|---|---:|---|
| 1 | GOLF_20260608_020_beicicc_task366_probe | 0.549732 | operator_family_replacement | medium | 1 | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 |
| 2 | GOLF_20260608_023_beicicc_task076_probe | 0.546613 | operator_family_replacement | medium | 1 | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 |
| 3 | GOLF_20260608_021_jsrdcht_memory_task255_probe | 0.250344 | operator_family_replacement | high | 1 | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 |
| 4 | GOLF_20260608_024_jsrdcht_memory_task285_probe | 0.244896 | operator_family_replacement | high | 1 | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 |
| 5 | GOLF_20260608_022_jonathan_task285_probe | 0.227764 | operator_family_replacement | medium | 1 | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX |
| 6 | GOLF_20260608_018_jonathan_task173_probe | 0.197199 | operator_family_replacement | medium | 1 | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX |
| 7 | GOLF_20260608_019_jonathan_top5_mix_probe | 0.160829 | operator_family_replacement | medium | 5 | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX |
| 8 | GOLF_20260608_017_jonathan_task286_probe | 0.098260 | single_task_probe | medium | 1 | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX |

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

## Negative Feedback Policy

Same-source, same-family, known-bad, low-upside, and broad-without-positive-probe signals reduce rank only. They do not block candidates that pass hard gates.

## Next Action

Submit all hard-gate eligible candidates through `scripts/19_submit_queue.py --submit-all-eligible --limit 999`.
