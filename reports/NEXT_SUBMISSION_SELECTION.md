# Next Submission Selection

checked_at: 2026-06-08T21:24:15
current_best: 6154.71 (GOLF_20260608_006_biohack_super_blend_structural_pass_mix)
candidate_count: 13
eligible_count: 3
blocked_count: 10
selected_candidate: GOLF_20260608_018_jonathan_task173_probe
selection_score: 0.572045
selection_reason: class=operator_family_replacement; AGS=0.728; structural_scale=0.95; source=0.65; upside=0.10; novelty=0.60; feedback=1.00; known_bad_penalty=0.00; small_tuning_penalty=0.00; recent_negative_source_penalty=0.40; same_family_negative_penalty=0.30; source_diversity_bonus=0.00; source_negative=recent negative source feedback from GOLF_20260608_008b_jonathan_structural_pass_mix, GOLF_20260608_016_jonathan_task233_probe, GOLF_20260608_016_jonathan_task255_probe; same_family_negative=same source already has negative bottom-tail probe feedback

## Top 10

| rank | exp_id | score | class | risk | tasks | source |
|---:|---|---:|---|---|---:|---|
| 1 | GOLF_20260608_018_jonathan_task173_probe | 0.572045 | operator_family_replacement | medium | 1 | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX |
| 2 | GOLF_20260608_019_jonathan_top5_mix_probe | 0.534805 | operator_family_replacement | medium | 5 | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX |
| 3 | GOLF_20260608_017_jonathan_task286_probe | 0.471887 | single_task_probe | medium | 1 | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX |

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

Same-source and same-family negative probes reduce rank but do not hard-block single-task probes. Broad mixes without positive probe feedback are blocked.

## Next Action

Submit `GOLF_20260608_018_jonathan_task173_probe` through `scripts/19_submit_queue.py --auto-select --limit 1`.
