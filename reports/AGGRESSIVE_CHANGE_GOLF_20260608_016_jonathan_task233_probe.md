# Aggressive Change: GOLF_20260608_016_jonathan_task233_probe

checked_at: 2026-06-08T20:37:20
AGS: 0.8840
classification: aggressive
submission_gate_pass: true
risk: medium

## Layers

- structural_delta: 0.9721
- semantic_risk_adjusted_validity: 0.9617
- competition_value: 0.5917
- novelty_and_source_strength: 0.9888

## Structural Delta

- op_family_delta: 0.9812
- topology_delta: 0.9818
- wl_subgraph_delta: 0.9940
- dataflow_path_delta: 0.9966
- initializer_structure_delta: 1.0000
- memory_profile_delta: 0.9996
- rewrite_class_score: 0.7500

## Rewrite Classes

- node_pruning_or_fusion: 1
- operator_family_rewrite: 1
- topology_rewrite: 1

## Differential Testing

- score: 1.0
- checked: 3
- base_candidate_matches: 3
- optimizer_level_matches: 3
- expected_passes: 3
- errors: 0
