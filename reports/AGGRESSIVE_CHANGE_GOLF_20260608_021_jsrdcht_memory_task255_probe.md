# Aggressive Change: GOLF_20260608_021_jsrdcht_memory_task255_probe

checked_at: 2026-06-08T22:14:00
AGS: 0.8425
classification: aggressive
submission_gate_pass: true
risk: high

## Layers

- structural_delta: 0.8246
- semantic_risk_adjusted_validity: 0.9617
- competition_value: 0.6547
- novelty_and_source_strength: 0.9298

## Structural Delta

- op_family_delta: 0.7027
- topology_delta: 0.6531
- wl_subgraph_delta: 0.8938
- dataflow_path_delta: 0.8972
- initializer_structure_delta: 1.0000
- memory_profile_delta: 0.9182
- rewrite_class_score: 0.7500

## Rewrite Classes

- initializer_elimination: 1
- operator_family_rewrite: 1
- topology_rewrite: 1

## Differential Testing

- score: 1.0
- checked: 3
- base_candidate_matches: 3
- optimizer_level_matches: 3
- expected_passes: 3
- errors: 0
