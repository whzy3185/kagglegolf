# Known Bad Families

updated_at: 2026-06-08T21:47:17

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
