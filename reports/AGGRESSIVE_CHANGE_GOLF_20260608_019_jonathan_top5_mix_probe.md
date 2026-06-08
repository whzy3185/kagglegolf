# Aggressive Change: GOLF_20260608_019_jonathan_top5_mix_probe

checked_at: 2026-06-08T21:20:22
AGS: 0.6992
classification: aggressive
submission_gate_pass: true
risk: medium

## Layers

- structural_delta: 0.5393
- semantic_risk_adjusted_validity: 0.9634
- competition_value: 0.5012
- novelty_and_source_strength: 0.8157

## Structural Delta

- op_family_delta: 0.4481
- topology_delta: 0.2491
- wl_subgraph_delta: 0.7357
- dataflow_path_delta: 0.7265
- initializer_structure_delta: 0.7453
- memory_profile_delta: 0.4383
- rewrite_class_score: 0.4000

## Rewrite Classes

- node_pruning_or_fusion: 2
- operator_family_rewrite: 4
- topology_rewrite: 2
- model_substitution: 1

## Differential Testing

- score: 1.0
- checked: 15
- base_candidate_matches: 15
- optimizer_level_matches: 15
- expected_passes: 15
- errors: 0
