# Aggressive Change: GOLF_20260607_004_public_notebook_full_replace

checked_at: 2026-06-08T20:03:32
AGS: 0.8319
classification: validation_fail
submission_gate_pass: false
risk: medium

## Layers

- structural_delta: 0.8850
- semantic_risk_adjusted_validity: 0.5993
- competition_value: 0.9817
- novelty_and_source_strength: 0.9540

## Structural Delta

- op_family_delta: 0.9259
- topology_delta: 0.8507
- wl_subgraph_delta: 0.9716
- dataflow_path_delta: 0.9143
- initializer_structure_delta: 0.8724
- memory_profile_delta: 0.8069
- rewrite_class_score: 0.7625

## Rewrite Classes

- initializer_elimination: 148
- topology_rewrite: 375
- node_pruning_or_fusion: 301
- operator_family_rewrite: 396
- model_substitution: 2

## Differential Testing

- score: 1.0
- checked: 72
- base_candidate_matches: 72
- optimizer_level_matches: 72
- expected_passes: 72
- errors: 0
