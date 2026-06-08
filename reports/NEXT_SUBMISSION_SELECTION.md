# Next Submission Selection

checked_at: 2026-06-09T00:51:39
current_best: 6272.50 (GOLF_20260608_025_kojimar_6272_full_replace)
candidate_count: 25
eligible_count: 1
blocked_count: 24
selected_candidate: GOLF_20260608_029_seddik_surgery_6272
selection_score: 0.633345
selection_reason: class=large_subgraph_rewrite; AGS=0.506; structural_scale=0.90; source=0.65; upside=0.45; novelty=1.00; attribution=0.55; tail_bonus=0.75; known_bad_penalty=0.00; small_tuning_penalty=0.00; recent_negative_source_penalty=0.00; same_family_negative_penalty=0.00; source_diversity_bonus=1.00; risk_penalty=0.35

policy: selection is ordering only, not a blocking gate
soft_penalties: affect submit order only; hard blocks are local validation, evidence gate, AGS gate, missing artifact, empty changed_tasks, already submitted, or explicit validation/evidence/metadata failure.

## Eligible Submit Order

| order | exp_id | score | soft_penalties |
|---:|---|---:|---|
| 1 | GOLF_20260608_029_seddik_surgery_6272 | 0.633345 | none |

## Top 10

| rank | exp_id | score | class | risk | tasks | source |
|---:|---|---:|---|---|---:|---|
| 1 | GOLF_20260608_029_seddik_surgery_6272 | 0.633345 | large_subgraph_rewrite | medium | 20 | SRC_KAGGLE_NOTEBOOK_SEDDIK_SURGICAL_ONNX |

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

## Negative Feedback Policy

Same-source, same-family, known-bad, low-upside, and broad-without-positive-probe signals reduce rank only. They do not block candidates that pass hard gates.

## Next Action

Submit all hard-gate eligible candidates through `scripts/19_submit_queue.py --submit-all-eligible --limit 999`.
