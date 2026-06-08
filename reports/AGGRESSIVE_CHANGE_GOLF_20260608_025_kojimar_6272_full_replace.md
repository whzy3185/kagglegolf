# Aggressive Change: GOLF_20260608_025_kojimar_6272_full_replace

checked_at: 2026-06-08T22:46:14
AGS: 0.6395
classification: strong
submission_gate_pass: true
risk: medium

## Layers

- structural_delta: 0.2234
- semantic_risk_adjusted_validity: 0.9697
- competition_value: 0.7553
- novelty_and_source_strength: 0.6893

## Structural Delta

- op_family_delta: 0.1159
- topology_delta: 0.0823
- wl_subgraph_delta: 0.2881
- dataflow_path_delta: 0.2357
- initializer_structure_delta: 0.3747
- memory_profile_delta: 0.3438
- rewrite_class_score: 0.1775

## Rewrite Classes

- model_substitution: 242
- initializer_elimination: 124
- operator_family_rewrite: 73
- node_pruning_or_fusion: 37
- topology_rewrite: 50

## Differential Testing

- score: 1.0
- checked: 72
- base_candidate_matches: 72
- optimizer_level_matches: 72
- expected_passes: 72
- errors: 0
