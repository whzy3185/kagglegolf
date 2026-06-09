# Top Task Implementation Queue

updated_at: 2026-06-09T12:11:16+00:00

source: `data/kaggle_code_single_task/public_vs_current_comparison.csv`

Selection rule: prefer verified public ONNX local improvement, then bottom-tail/high-cost tasks. Known public-LB negative probes are annotated and deprioritized, not erased.

| rank | task | source | estimated_gain | current_cost | public_cost | bottom_tail | high_memory | action | note |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | task233 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 3.087910 | 1656727.0 | 75542 | true | true | skip_for_now_known_negative_probe | negative_lb_probe_6144_03_delta_minus_10_68 |
| 2 | task076 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 2.210760 | 330094.0 | 36184 | false | true | direct_single_task_replacement |  |
| 3 | task096 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 1.885155 | 193458.0 | 29368 | false | true | direct_single_task_replacement |  |
| 4 | task101 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 1.737649 | 374431.0 | 65875 | false | true | direct_single_task_replacement |  |
| 5 | task255 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 1.508678 | 645586.0 | 142805 | true | true | direct_single_task_replacement |  |
| 6 | task018 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 1.424549 | 476184.0 | 114578 | true | true | direct_single_task_replacement |  |
| 7 | task066 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 1.573098 | 103220.0 | 21408 | false | true | direct_single_task_replacement |  |
| 8 | task023 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 1.164118 | 68652.0 | 21433 | false | false | direct_single_task_replacement |  |
| 9 | task285 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.823334 | 395466.0 | 173596 | true | true | direct_single_task_replacement |  |
| 10 | task175 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 1.065278 | 94820.0 | 32678 | false | false | direct_single_task_replacement |  |
| 11 | task243 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.473324 | 108966.0 | 67878 | true | true | direct_single_task_replacement |  |
| 12 | task118 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.661275 | 116286.0 | 60026 | false | true | direct_single_task_replacement |  |
| 13 | task025 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.450462 | 140093.0 | 89286 | true | true | direct_single_task_replacement |  |
| 14 | task153 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.620763 | 21394.0 | 11500 | false | false | direct_single_task_replacement |  |
| 15 | task209 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.471777 | 122356.0 | 76337 | false | true | direct_single_task_replacement |  |
| 16 | task219 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.566778 | 84847.0 | 48138 | false | false | direct_single_task_replacement |  |
| 17 | task319 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.557678 | 33507.0 | 19184 | false | false | direct_single_task_replacement |  |
| 18 | task158 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.046396 | 191458.0 | 182778 | true | true | direct_single_task_replacement |  |
| 19 | task044 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.278094 | 42002.0 | 31805 | false | false | direct_single_task_replacement |  |
| 20 | task191 | jonathanchan__ngc26-constraint-smart-logic-mix-blending | 0.149434 | 85919.0 | 73993 | false | false | direct_single_task_replacement |  |
