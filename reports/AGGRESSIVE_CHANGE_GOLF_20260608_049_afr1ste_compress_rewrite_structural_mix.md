# Aggressive Change: GOLF_20260608_049_afr1ste_compress_rewrite_structural_mix

checked_at: 2026-06-09T12:35:57
AGS: 0.8582
classification: aggressive
submission_gate_pass: true
risk: high
content_changed_task_count: 369

## Layers

- structural_delta: 0.6907
- semantic_risk_adjusted_validity: 0.9697
- competition_value: 0.9340
- novelty_and_source_strength: 0.8763

## Structural Delta

- op_family_delta: 0.5700
- topology_delta: 0.4475
- wl_subgraph_delta: 0.8201
- dataflow_path_delta: 0.8083
- initializer_structure_delta: 0.9244
- memory_profile_delta: 0.6812
- rewrite_class_score: 0.6165

## Rewrite Classes

- initializer_elimination: 247
- operator_family_rewrite: 332
- topology_rewrite: 290
- node_pruning_or_fusion: 41
- model_substitution: 32

## Differential Testing

- score: 1.0
- checked: 72
- base_candidate_matches: 72
- optimizer_level_matches: 72
- expected_passes: 72
- errors: 0
