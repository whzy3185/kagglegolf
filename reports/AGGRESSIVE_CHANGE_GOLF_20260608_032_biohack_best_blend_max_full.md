# Aggressive Change: GOLF_20260608_032_biohack_best_blend_max_full

checked_at: 2026-06-09T02:03:08
AGS: 0.5886
classification: strong
submission_gate_pass: true
risk: medium

## Layers

- structural_delta: 0.0746
- semantic_risk_adjusted_validity: 0.9697
- competition_value: 0.7800
- novelty_and_source_strength: 0.6298

## Structural Delta

- op_family_delta: 0.0262
- topology_delta: 0.0153
- wl_subgraph_delta: 0.0886
- dataflow_path_delta: 0.0621
- initializer_structure_delta: 0.1507
- memory_profile_delta: 0.1841
- rewrite_class_score: 0.0194

## Rewrite Classes

- model_substitution: 382
- initializer_elimination: 7
- operator_family_rewrite: 12
- topology_rewrite: 8
- node_pruning_or_fusion: 4

## Differential Testing

- score: 1.0
- checked: 72
- base_candidate_matches: 72
- optimizer_level_matches: 72
- expected_passes: 72
- errors: 0
