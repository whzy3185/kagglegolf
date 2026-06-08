# Aggressive Change: GOLF_20260608_031_beicicc_inline_396_mix

checked_at: 2026-06-09T01:20:26
AGS: 0.8475
classification: aggressive
submission_gate_pass: true
risk: medium

## Layers

- structural_delta: 0.6339
- semantic_risk_adjusted_validity: 0.9697
- competition_value: 0.9811
- novelty_and_source_strength: 0.8536

## Structural Delta

- op_family_delta: 0.5053
- topology_delta: 0.3820
- wl_subgraph_delta: 0.7731
- dataflow_path_delta: 0.7500
- initializer_structure_delta: 0.8954
- memory_profile_delta: 0.6589
- rewrite_class_score: 0.4830

## Rewrite Classes

- initializer_elimination: 127
- topology_rewrite: 248
- operator_family_rewrite: 320
- model_substitution: 66
- node_pruning_or_fusion: 70

## Differential Testing

- score: 1.0
- checked: 72
- base_candidate_matches: 72
- optimizer_level_matches: 72
- expected_passes: 72
- errors: 0
