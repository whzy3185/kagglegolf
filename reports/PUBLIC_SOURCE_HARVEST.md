# Public Source Harvest

Last updated: 2026-06-08T17:31:47

## Submitted Sources

| exp_id | source_id | source | candidate type | local validation | submission_id | public_score | decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GOLF_20260608_004b_beicicc_structural_pass_mix | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 | beicicc/neurogolf-6645-39-public-score-open-solution | 79-task structural-pass mix | pass, 1200/1200 | 53472483 | 5948.07 | reject as broad mix; retain source for task-level probes only |
| GOLF_20260608_008b_jonathan_structural_pass_mix | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | jonathanchan/ngc26-constraint-smart-logic-mix-blending | 397-task structural-pass mix | pass, 1200/1200 | 53472715 | 5595.78 | reject as broad mix; probe individual high-value tasks before reuse |

## Failed Local Candidates

| exp_id | source_id | reason | next action |
| --- | --- | --- | --- |
| GOLF_20260607_004_public_notebook_full_replace | SRC_KAGGLE_NOTEBOOK_BEICICC_6645 | bad_opset_domain:golf, has_functions, banned Compress ops | only use structural-pass or normalized tasks |
| GOLF_20260608_008_jonathan_constraint_logic_mix | SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | task076/task243 banned Compress; task102 example failures | use 008b structural-pass mix and targeted probes |

## Download Status

| source_id | slug | output status | notes |
| --- | --- | --- | --- |
| SRC_KAGGLE_NOTEBOOK_MIRZA_BEST_SCORE | mirzayasirabdullah07/best-score-neurogolf-championship-notebook | partial task output downloaded | 308 task files available from _src_A; no submission.zip found in first page |
| SRC_KAGGLE_NOTEBOOK_BIOHACK_SUPER_BLEND | biohack44/neurogolf-super-blend-best-public-score | partial task output downloaded | 288 task files available from _src_A; no submission.zip found in first page |
| SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX | jonathanchan/ngc26-constraint-smart-logic-mix-blending | submission.zip downloaded | 401 files task000-task400; task001-task400 standardized for validation |

## Next Actions

1. Build Mirza structural-pass candidate from available `_src_A` tasks, then submit if validator passes.
2. Build Biohack structural-pass candidate from available `_src_A` tasks, then submit if validator passes.
3. Avoid broad replacement with Jonathan or Beicicc unless task-level probes show positive contribution.
