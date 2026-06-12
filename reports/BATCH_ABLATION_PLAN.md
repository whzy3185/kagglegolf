# Batch Ablation Plan

updated_at: 2026-06-11T23:09:50
positive_batch_count: 1
negative_batch_count: 5
pending_or_unscored_count: 5
ablation_needed_count: 5

## Batch Outcomes

| exp_id | tasks | score | delta_parent | outcome | child_exp_ids |
|---|---:|---:|---:|---|---|
| GOLF_20260610_080_simple_exact_batch_conservative_5 | 5 | 6281.07 | -11.370000 | negative_batch | GOLF_20260610_081_simple_exact_batch_080_A2,GOLF_20260610_082_simple_exact_batch_080_B3 |
| GOLF_20260610_081_simple_exact_batch_080_A2 | 2 | 6289.61 | -2.830000 | negative_batch | GOLF_20260610_082_simple_exact_batch_081_A1,GOLF_20260610_083_simple_exact_batch_081_B1 |
| GOLF_20260610_081_simple_exact_batch_medium_10 | 4 | 6292.94 | 0.500000 | positive_batch |  |
| GOLF_20260610_082_simple_exact_batch_080_B3 | 3 | 6283.90 | -8.540000 | negative_batch | GOLF_20260610_083_simple_exact_batch_082_A1,GOLF_20260610_084_simple_exact_batch_082_B2 |
| GOLF_20260610_082_simple_exact_batch_081_A1 | 1 |  |  | pending_or_unscored |  |
| GOLF_20260610_082_simple_exact_batch_aggressive_20 | 11 | 6268.28 | -24.160000 | negative_batch | GOLF_20260610_083_simple_exact_batch_082_A5,GOLF_20260610_084_simple_exact_batch_082_B6 |
| GOLF_20260610_083_simple_exact_batch_081_B1 | 1 |  |  | pending_or_unscored |  |
| GOLF_20260610_083_simple_exact_batch_082_A1 | 1 |  |  | pending_or_unscored |  |
| GOLF_20260610_083_simple_exact_batch_082_A5 | 5 | 6281.07 | -11.370000 | negative_batch | GOLF_20260610_084_simple_exact_batch_083_A2,GOLF_20260610_085_simple_exact_batch_083_B3 |
| GOLF_20260610_084_simple_exact_batch_082_B2 | 2 |  |  | pending_or_unscored |  |
| GOLF_20260610_084_simple_exact_batch_082_B6 | 6 |  |  | pending_or_unscored |  |

## Positive Batch

- GOLF_20260610_081_simple_exact_batch_medium_10

## Negative Batch

- GOLF_20260610_080_simple_exact_batch_conservative_5
- GOLF_20260610_082_simple_exact_batch_aggressive_20
- GOLF_20260610_081_simple_exact_batch_080_A2
- GOLF_20260610_082_simple_exact_batch_080_B3
- GOLF_20260610_083_simple_exact_batch_082_A5

## Need Binary Ablation

- GOLF_20260610_080_simple_exact_batch_conservative_5
- GOLF_20260610_082_simple_exact_batch_aggressive_20
- GOLF_20260610_081_simple_exact_batch_080_A2
- GOLF_20260610_082_simple_exact_batch_080_B3
- GOLF_20260610_083_simple_exact_batch_082_A5

## Build Log

No child candidates built in this run.
