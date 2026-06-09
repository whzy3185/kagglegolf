# Known Bad Families

updated_at: 2026-06-09T14:12:43

This file is consumed by the automatic selector. It records negative leaderboard feedback that should penalize similar candidates without deleting the source from the alternate task pool.

## Explicit Rules

| exp_id | source_id | task_or_bundle | score | delta_parent | decision | selector_rule |
|---|---|---|---:|---:|---|---|
| GOLF_20260607_002_public_6029_aggressive_mix | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task054 | 6154.59 | -0.120000 | negative_or_mixed | do_not_repeat_same_6029_small_mix |
| GOLF_20260607_003_bottom15_single_task_probe | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task286 | 6154.67 | -0.040000 | rejected_for_current_base | task286/jsrdcht_6029 not confirmed for current base |
| GOLF_20260608_004b_beicicc_structural_pass_mix | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 | bundle_79_tasks | 5948.07 | -206.640000 | bundle_negative | broad Beicicc structural-pass mix is known_bad_family; only allow targeted probe or normalized solver replacement |
| GOLF_20260608_008b_jonathan_structural_pass_mix | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | bundle_397_tasks | 5595.78 | -558.930000 | bundle_negative | broad Jonathan structural-pass mix is known_bad_family; only allow targeted single-task probes with source diversity controls |
| GOLF_20260608_016_jonathan_task233_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task233 | 6144.03 | -10.680000 | rejected_for_current_base | task233/Jonathan not confirmed; penalize same-source bottom-tail structural probes until source diversity or positive probe exists |

## All Negative Feedback

| exp_id | source_id | task_or_bundle | count | score | delta_parent | decision |
|---|---|---|---:|---:|---:|---|
| GOLF_20260607_002_public_6029_aggressive_mix | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task286 | 3 | 6154.59 | -0.120000 | negative_or_mixed |
| GOLF_20260607_002_public_6029_aggressive_mix | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task173 | 3 | 6154.59 | -0.120000 | negative_or_mixed |
| GOLF_20260607_002_public_6029_aggressive_mix | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task054 | 3 | 6154.59 | -0.120000 | negative_or_mixed |
| GOLF_20260607_003_bottom15_single_task_probe | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task286 | 1 | 6154.67 | -0.040000 | rejected_for_current_base |
| GOLF_20260608_004b_beicicc_structural_pass_mix | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 | bundle_79_tasks | 79 | 5948.07 | -206.640000 | bundle_negative |
| GOLF_20260608_008b_jonathan_structural_pass_mix | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | bundle_397_tasks | 397 | 5595.78 | -558.930000 | bundle_negative |
| GOLF_20260608_016_jonathan_task233_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task233 | 1 | 6144.03 | -10.680000 | rejected_for_current_base |
| GOLF_20260608_016_jonathan_task255_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task255 | 1 | 6144.05 | -10.660000 | rejected_for_current_base |
| GOLF_20260608_017_jonathan_task286_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task286 | 1 | 6153.76 | -0.950000 | rejected_for_current_base |
| GOLF_20260608_018_jonathan_task173_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task173 | 1 | 6153.77 | -0.940000 | rejected_for_current_base |
| GOLF_20260608_019_jonathan_top5_mix_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task187 | 5 | 6139.85 | -14.860000 | negative_or_mixed |
| GOLF_20260608_019_jonathan_top5_mix_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task018 | 5 | 6139.85 | -14.860000 | negative_or_mixed |
| GOLF_20260608_019_jonathan_top5_mix_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task054 | 5 | 6139.85 | -14.860000 | negative_or_mixed |
| GOLF_20260608_019_jonathan_top5_mix_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task349 | 5 | 6139.85 | -14.860000 | negative_or_mixed |
| GOLF_20260608_019_jonathan_top5_mix_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task145 | 5 | 6139.85 | -14.860000 | negative_or_mixed |
| GOLF_20260608_020_beicicc_task366_probe | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 | task366 | 1 | 6143.61 | -11.100000 | rejected_for_current_base |
| GOLF_20260608_021_jsrdcht_memory_task255_probe | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task255 | 1 | 6151.46 | -3.250000 | rejected_for_current_base |
| GOLF_20260608_022_jonathan_task285_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task285 | 1 | 6142.81 | -11.900000 | rejected_for_current_base |
| GOLF_20260608_023_beicicc_task076_probe | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 | task076 | 1 | 6142.58 | -12.130000 | rejected_for_current_base |
| GOLF_20260608_024_jsrdcht_memory_task285_probe | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task285 | 1 | 6148.79 | -5.920000 | rejected_for_current_base |
| GOLF_20260608_014_biohack_task187_probe | SRC_KAGGLE_NOTEBOOK_BIOHACK_SUPER_BLEND | task187 | 1 | 6272.26 | -0.240000 | rejected_for_current_base |
| GOLF_20260608_012_mirza_task187_probe | SRC_KAGGLE_NOTEBOOK_MIRZA_BEST_SCORE | task187 | 1 | 6272.26 | -0.240000 | rejected_for_current_base |
| GOLF_20260608_026_beicicc_task169_probe | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 | task169 | 1 | 6269.97 | -2.530000 | rejected_for_current_base |
| GOLF_20260608_027_jsrdcht_memory_task018_probe | SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | task018 | 1 | 6271.90 | -0.600000 | rejected_for_current_base |
| GOLF_20260608_028_jonathan_task025_probe | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task025 | 1 | 6259.35 | -13.150000 | rejected_for_current_base |
| GOLF_20260608_031_beicicc_inline_396_mix | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 | bundle_396_tasks | 396 | 5043.59 | -1229.010000 | bundle_negative |
| GOLF_20260608_032_biohack_best_blend_max_full | SRC_KAGGLE_NOTEBOOK_BIOHACK_BEST_BLEND_MAX_PUBLIC | bundle_400_tasks | 400 | 6255.14 | -17.460000 | bundle_negative |
| GOLF_20260608_034_rogermt_6273_full_replace | SRC_HF_ROGERMT_6273_SUBMISSION | bundle_400_tasks | 400 | 6272.50 | -0.100000 | bundle_negative |
| GOLF_20260608_037_rogermt_task062_optimized_probe | SRC_HF_ROGERMT_6273_SUBMISSION | task062 | 1 | 6272.54 | -0.060000 | rejected_for_current_base |
| GOLF_20260608_038_rogermt_task243_optimized_probe | SRC_HF_ROGERMT_6273_SUBMISSION | task243 | 1 | 6272.19 | -0.410000 | rejected_for_current_base |
| GOLF_20260608_041_rogermt_task153_after020_probe | SRC_HF_ROGERMT_6273_SUBMISSION | task153 | 1 | 6275.05 | -0.020000 | rejected_for_current_base |
| GOLF_20260608_044_rogermt_task092_after020_probe | SRC_HF_ROGERMT_6273_SUBMISSION | task092 | 1 | 6274.06 | -1.010000 | rejected_for_current_base |
| GOLF_20260608_047b_vyanktesh_except_task133 | SRC_KAGGLE_NOTEBOOK_VYANKTESH_MULTI_SOURCE | bundle_399_tasks | 399 | 6235.30 | -43.020000 | bundle_negative |
| GOLF_20260608_048b_afr1ste_6335_structural_pass_mix | SRC_KAGGLE_DATASET_AFR1STE_6335 | bundle_123_tasks | 123 | 4894.51 | -1383.810000 | bundle_negative |
| GOLF_20260608_049_afr1ste_compress_rewrite_structural_mix | SRC_KAGGLE_DATASET_AFR1STE_6335 | bundle_369_tasks | 369 | 3450.39 | -2827.930000 | bundle_negative |
