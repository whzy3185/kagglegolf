# Batch Ablation Plan

updated_at: 2026-06-12T21:05:22
positive_batch_count: 2
negative_batch_count: 16
pending_or_unscored_count: 1
ablation_needed_count: 16

## Batch Outcomes

| exp_id | tasks | score | delta_parent | outcome | child_exp_ids |
|---|---:|---:|---:|---|---|
| GOLF_20260610_080_simple_exact_batch_conservative_5 | 5 | 6281.07 | -11.370000 | negative_batch | GOLF_20260610_081_simple_exact_batch_080_A2,GOLF_20260610_082_simple_exact_batch_080_B3 |
| GOLF_20260610_081_simple_exact_batch_080_A2 | 2 | 6289.61 | -2.830000 | negative_batch | GOLF_20260610_082_simple_exact_batch_081_A1,GOLF_20260610_083_simple_exact_batch_081_B1 |
| GOLF_20260610_081_simple_exact_batch_medium_10 | 4 | 6292.94 | 0.500000 | positive_batch |  |
| GOLF_20260610_082_simple_exact_batch_080_B3 | 3 | 6283.90 | -8.540000 | negative_batch | GOLF_20260610_083_simple_exact_batch_082_A1,GOLF_20260610_084_simple_exact_batch_082_B2 |
| GOLF_20260610_082_simple_exact_batch_081_A1 | 1 | 6292.16 | -0.280000 | negative_batch |  |
| GOLF_20260610_082_simple_exact_batch_aggressive_20 | 11 | 6268.28 | -24.160000 | negative_batch | GOLF_20260610_083_simple_exact_batch_082_A5,GOLF_20260610_084_simple_exact_batch_082_B6 |
| GOLF_20260610_083_simple_exact_batch_081_B1 | 1 | 6289.90 | -2.540000 | negative_batch |  |
| GOLF_20260610_083_simple_exact_batch_082_A1 | 1 | 6289.90 | -2.540000 | negative_batch |  |
| GOLF_20260610_083_simple_exact_batch_082_A5 | 5 | 6281.07 | -11.370000 | negative_batch | GOLF_20260610_084_simple_exact_batch_083_A2,GOLF_20260610_085_simple_exact_batch_083_B3 |
| GOLF_20260610_084_simple_exact_batch_082_B2 | 2 | 6286.45 | -5.990000 | negative_batch | GOLF_20260610_085_simple_exact_batch_084_A1,GOLF_20260610_086_simple_exact_batch_084_B1 |
| GOLF_20260610_084_simple_exact_batch_082_B6 | 6 | 6279.65 | -12.790000 | negative_batch | GOLF_20260610_085_simple_exact_batch_084_A3,GOLF_20260610_086_simple_exact_batch_084_B3 |
| GOLF_20260610_085_simple_exact_batch_084_A1 | 1 | 6289.45 | -2.990000 | negative_batch |  |
| GOLF_20260610_085_simple_exact_batch_084_A3 | 3 | 6286.99 | -5.450000 | negative_batch | GOLF_20260610_086_simple_exact_batch_085_A1,GOLF_20260610_087_simple_exact_batch_085_B2 |
| GOLF_20260610_086_simple_exact_batch_084_B1 | 1 | 6289.45 | -2.990000 | negative_batch |  |
| GOLF_20260610_086_simple_exact_batch_084_B3 | 3 | 6285.10 | -7.340000 | negative_batch | GOLF_20260610_087_simple_exact_batch_086_A1,GOLF_20260610_088_simple_exact_batch_086_B2 |
| GOLF_20260610_086_simple_exact_batch_085_A1 | 1 | 6292.08 | -0.360000 | negative_batch |  |
| GOLF_20260610_087_simple_exact_batch_085_B2 | 2 | 6287.36 | -5.080000 | negative_batch | GOLF_20260610_088_simple_exact_batch_087_A1,GOLF_20260610_089_simple_exact_batch_087_B1 |
| GOLF_20260610_087_simple_exact_batch_086_A1 | 1 | 6293.07 | 0.630000 | positive_batch |  |
| GOLF_20260610_088_simple_exact_batch_086_B2 | 2 |  |  | pending_or_unscored |  |

## Positive Batch

- GOLF_20260610_081_simple_exact_batch_medium_10
- GOLF_20260610_087_simple_exact_batch_086_A1

## Negative Batch

- GOLF_20260610_080_simple_exact_batch_conservative_5
- GOLF_20260610_082_simple_exact_batch_aggressive_20
- GOLF_20260610_081_simple_exact_batch_080_A2
- GOLF_20260610_082_simple_exact_batch_080_B3
- GOLF_20260610_083_simple_exact_batch_082_A5
- GOLF_20260610_084_simple_exact_batch_082_B6
- GOLF_20260610_082_simple_exact_batch_081_A1
- GOLF_20260610_083_simple_exact_batch_081_B1
- GOLF_20260610_083_simple_exact_batch_082_A1
- GOLF_20260610_084_simple_exact_batch_082_B2
- GOLF_20260610_085_simple_exact_batch_084_A3
- GOLF_20260610_086_simple_exact_batch_084_B3
- GOLF_20260610_085_simple_exact_batch_084_A1
- GOLF_20260610_086_simple_exact_batch_084_B1
- GOLF_20260610_086_simple_exact_batch_085_A1
- GOLF_20260610_087_simple_exact_batch_085_B2

## Need Binary Ablation

- GOLF_20260610_080_simple_exact_batch_conservative_5
- GOLF_20260610_082_simple_exact_batch_aggressive_20
- GOLF_20260610_081_simple_exact_batch_080_A2
- GOLF_20260610_082_simple_exact_batch_080_B3
- GOLF_20260610_083_simple_exact_batch_082_A5
- GOLF_20260610_084_simple_exact_batch_082_B6
- GOLF_20260610_082_simple_exact_batch_081_A1
- GOLF_20260610_083_simple_exact_batch_081_B1
- GOLF_20260610_083_simple_exact_batch_082_A1
- GOLF_20260610_084_simple_exact_batch_082_B2
- GOLF_20260610_085_simple_exact_batch_084_A3
- GOLF_20260610_086_simple_exact_batch_084_B3
- GOLF_20260610_085_simple_exact_batch_084_A1
- GOLF_20260610_086_simple_exact_batch_084_B1
- GOLF_20260610_086_simple_exact_batch_085_A1
- GOLF_20260610_087_simple_exact_batch_085_B2

## Build Log

- GOLF_20260610_081_simple_exact_batch_080_A2: already exists
- GOLF_20260610_082_simple_exact_batch_080_B3: already exists
- GOLF_20260610_083_simple_exact_batch_082_A5: duplicate task set of GOLF_20260610_080_simple_exact_batch_conservative_5; skipped
- GOLF_20260610_084_simple_exact_batch_082_B6: already exists
- GOLF_20260610_082_simple_exact_batch_081_A1: already exists
- GOLF_20260610_083_simple_exact_batch_081_B1: already exists
- GOLF_20260610_083_simple_exact_batch_082_A1: already exists
- GOLF_20260610_084_simple_exact_batch_082_B2: already exists
- GOLF_20260610_084_simple_exact_batch_083_A2: duplicate task set of GOLF_20260610_081_simple_exact_batch_080_A2; skipped
- GOLF_20260610_085_simple_exact_batch_083_B3: duplicate task set of GOLF_20260610_082_simple_exact_batch_080_B3; skipped
- GOLF_20260610_085_simple_exact_batch_084_A3: already exists
- GOLF_20260610_086_simple_exact_batch_084_B3: already exists
- GOLF_20260610_085_simple_exact_batch_084_A1: already exists
- GOLF_20260610_086_simple_exact_batch_084_B1: already exists
- GOLF_20260610_086_simple_exact_batch_085_A1: already exists
- GOLF_20260610_087_simple_exact_batch_085_B2: already exists
- GOLF_20260610_087_simple_exact_batch_086_A1: already exists
- GOLF_20260610_088_simple_exact_batch_086_B2: already exists
- GOLF_20260610_088_simple_exact_batch_087_A1: returncode=0; E:\kagglegolf\submissions\candidates\GOLF_20260610_088_simple_exact_batch_087_A1
changed_tasks task166
changed_task_count 1
validation_ok True
- GOLF_20260610_089_simple_exact_batch_087_B1: returncode=0; E:\kagglegolf\submissions\candidates\GOLF_20260610_089_simple_exact_batch_087_B1
changed_tasks task276
changed_task_count 1
validation_ok True
