# Batch Ablation Plan

updated_at: 2026-06-11T22:56:23
positive_batch_count: 1
negative_batch_count: 2
pending_or_unscored_count: 0
ablation_needed_count: 2

## Batch Outcomes

| exp_id | tasks | score | delta_parent | outcome | child_exp_ids |
|---|---:|---:|---:|---|---|
| GOLF_20260610_080_simple_exact_batch_conservative_5 | 5 | 6281.07 | -11.370000 | negative_batch | GOLF_20260610_081_simple_exact_batch_080_A2,GOLF_20260610_082_simple_exact_batch_080_B3 |
| GOLF_20260610_081_simple_exact_batch_medium_10 | 4 | 6292.94 | 0.500000 | positive_batch |  |
| GOLF_20260610_082_simple_exact_batch_aggressive_20 | 11 | 6268.28 | -24.160000 | negative_batch | GOLF_20260610_083_simple_exact_batch_082_A5,GOLF_20260610_084_simple_exact_batch_082_B6 |

## Positive Batch

- GOLF_20260610_081_simple_exact_batch_medium_10

## Negative Batch

- GOLF_20260610_080_simple_exact_batch_conservative_5
- GOLF_20260610_082_simple_exact_batch_aggressive_20

## Need Binary Ablation

- GOLF_20260610_080_simple_exact_batch_conservative_5
- GOLF_20260610_082_simple_exact_batch_aggressive_20

## Build Log

- GOLF_20260610_081_simple_exact_batch_080_A2: returncode=0; E:\kagglegolf\submissions\candidates\GOLF_20260610_081_simple_exact_batch_080_A2
changed_tasks task031,task087
changed_task_count 2
validation_ok True
- GOLF_20260610_082_simple_exact_batch_080_B3: returncode=0; E:\kagglegolf\submissions\candidates\GOLF_20260610_082_simple_exact_batch_080_B3
changed_tasks task140,task223,task307
changed_task_count 3
validation_ok True
- GOLF_20260610_083_simple_exact_batch_082_A5: returncode=0; E:\kagglegolf\submissions\candidates\GOLF_20260610_083_simple_exact_batch_082_A5
changed_tasks task031,task087,task140,task223,task307
changed_task_count 5
validation_ok True
- GOLF_20260610_084_simple_exact_batch_082_B6: returncode=0; E:\kagglegolf\submissions\candidates\GOLF_20260610_084_simple_exact_batch_082_B6
changed_tasks task036,task166,task276,task300,task309,task380
changed_task_count 6
validation_ok True
