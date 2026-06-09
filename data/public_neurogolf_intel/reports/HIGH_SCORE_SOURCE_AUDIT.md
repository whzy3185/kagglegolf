# High-Score Source Audit

checked_at: 2026-06-09T12:05:16+00:00

## Current High-Score Signal

- Top public leaderboard is above 7700, so the 7000 target requires high-score source harvest and task-level replacement, not local micro-tuning.
- Discussion evidence confirms order-sensitivity and Conv bias pitfalls can make local/LB mismatch; every extracted ONNX must be package-validated before submission.

## Discussion Leads

| topic | relevance | action |
|---|---|---|
| Released a 6029.09 LB all-task ONNX bundle | public all-task bundle and cost reduction advice | already extracted and compared as public ONNX source |
| Scoring differs between single-file and full-bundle submissions | warns task-level local gains may not translate to LB | build only one-task probes and keep task attribution |
| order sensitivity bug? | warns malformed Conv bias and zip/order effects | run full package validator and avoid malformed Conv artifacts |
| 4743.93 task table / pack inspection | dashboard/task-table precedent and public resources | use as low-priority task-table/source pattern |

## Kaggle Code Harvest Summary

| source | public_onnx_scored | verified_local_wins |
|---|---:|---:|
| jonathanchan__ngc26-constraint-smart-logic-mix-blending | 325 | 20 |
| octaviograu__6154-71-onnx-rewrites-hand-built-solvers | 3 | 0 |

## Top Verified Public ONNX Local Wins

| rank | task | source | public_score | current_score | delta | public_cost |
|---:|---|---|---:|---:|---:|---:|
| 1 | task233 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.767555928044851 | 10.679645472747369 | 3.0879104552974823 | 75542 |
| 2 | task076 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 14.503627688842322 | 12.292867258634116 | 2.2107604302082056 | 36184 |
| 3 | task096 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 14.71233907482333 | 12.827184286371278 | 1.885154788452052 | 29368 |
| 4 | task101 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.904485714156337 | 12.166837180696787 | 1.7376485334595504 | 65875 |
| 5 | task066 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 15.028480037072045 | 13.455382088297283 | 1.5730979487747625 | 21408 |
| 6 | task255 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.130764657719753 | 11.62208628955128 | 1.5086783681684732 | 142805 |
| 7 | task018 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.35098890724301 | 11.926440386857584 | 1.424548520385427 | 114578 |
| 8 | task023 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 15.027312930662868 | 13.863194455943471 | 1.1641184747193964 | 21433 |
| 9 | task175 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 14.60554265240923 | 13.54026436354389 | 1.0652782888653398 | 32678 |
| 10 | task285 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 12.935513960531726 | 12.112179904635754 | 0.8233340558959714 | 173596 |
| 11 | task118 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.997466919324204 | 13.336192047071197 | 0.6612748722530064 | 60026 |
| 12 | task153 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 15.649897685648659 | 15.029134212133924 | 0.6207634735147352 | 11500 |
| 13 | task219 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 14.218172835018288 | 13.651395086474174 | 0.5667777485441139 | 48138 |
| 14 | task319 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 15.138168122732704 | 14.580490348791063 | 0.5576777739416414 | 19184 |
| 15 | task243 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.874532744845478 | 13.401208814053447 | 0.4733239307920307 | 67878 |
| 16 | task209 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.757086972350876 | 13.28530989269121 | 0.47177707965966675 | 76337 |
| 17 | task025 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.600400020341894 | 13.149938233234366 | 0.45046178710752827 | 89286 |
| 18 | task044 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 14.632621210887095 | 14.354527484820627 | 0.27809372606646754 | 31805 |
| 19 | task191 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 13.788274226882638 | 13.638839729058745 | 0.1494344978238935 | 73993 |
| 20 | task158 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 12.883972419349877 | 12.837576257600388 | 0.046396161749489906 | 182778 |
