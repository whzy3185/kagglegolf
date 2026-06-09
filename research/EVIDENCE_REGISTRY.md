# Evidence Registry

All external sources used for candidates must be listed here before entering an experiment.

## SRC_OFFICIAL_COMPETITION

source_id: SRC_OFFICIAL_COMPETITION
source_type: competition
title: The 2026 NeuroGolf Championship
author_or_team: Neurosynthetic Research Institute / Kaggle
url_or_identifier: https://www.kaggle.com/competitions/neurogolf-2026
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: all
idea_summary: Official task, scoring, and submission contract.
implementation_hint: Use `task001.onnx` through `task400.onnx` in `submission.zip`.
risk: low
rule_status: official
repro_status: reproduced
priority: P0
assigned_exp_id: GOLF_20260607_001_public_6154_repro

## SRC_OFFICIAL_UTILS

source_id: SRC_OFFICIAL_UTILS
source_type: code
title: neurogolf_utils.py
author_or_team: Google LLC / competition host
url_or_identifier: data/raw/neurogolf-2026/neurogolf_utils/neurogolf_utils.py
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: all
idea_summary: Official local validator and scorer behavior; bans Compress in addition to page-listed ops.
implementation_hint: Mirror tensor names, shape, dtype, opset, file limit, and banned-op checks.
risk: low
rule_status: official
repro_status: reproduced
priority: P0
assigned_exp_id: GOLF_20260607_001_public_6154_repro

## SRC_KAGGLE_NOTEBOOK_OCTAVIO_6154

source_id: SRC_KAGGLE_NOTEBOOK_OCTAVIO_6154
source_type: notebook
title: [6154.71] ONNX Rewrites + Hand-Built Solvers
author_or_team: Octavi Grau
url_or_identifier: https://www.kaggle.com/code/octaviograu/6154-71-onnx-rewrites-hand-built-solvers
date_accessed: 2026-06-07
claimed_score: 6154.71
tasks_mentioned: all
idea_summary: Public high-score notebook combining manual rewrites and hand-built solvers.
implementation_hint: Pull notebook metadata and reproduce via public dataset `octaviograu/neurogolf-manual-rewrites-v205`.
risk: low
rule_status: public_source
repro_status: reproduced
priority: P0
assigned_exp_id: GOLF_20260607_001_public_6154_repro

## SRC_KAGGLE_DATASET_OCTAVIO_REWRITES_V205

source_id: SRC_KAGGLE_DATASET_OCTAVIO_REWRITES_V205
source_type: dataset
title: neurogolf-manual-rewrites-v205
author_or_team: Octavi Grau
url_or_identifier: https://www.kaggle.com/datasets/octaviograu/neurogolf-manual-rewrites-v205
date_accessed: 2026-06-07
claimed_score: 6154.71
tasks_mentioned: all
idea_summary: Complete public `submission/` directory with 400 ONNX task solvers and cost CSV.
implementation_hint: Copy `submission/task*.onnx`; Kaggle Notebook output uses this dataset directly.
risk: low
rule_status: CC0 public dataset
repro_status: reproduced
priority: P0
assigned_exp_id: GOLF_20260607_001_public_6154_repro

## SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029

source_id: SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029
source_type: notebook
title: [6029.09 LB] NeuroGolf All-Task ONNX Solution
author_or_team: Chet
url_or_identifier: https://www.kaggle.com/code/jsrdcht/6029-09-lb-neurogolf-all-task-onnx-solution
date_accessed: 2026-06-07
claimed_score: 6029.09
tasks_mentioned: all
idea_summary: Public all-task ONNX solution; major fallback and diff source.
implementation_hint: Pull dataset `jsrdcht/neurogolf-6029-submission-bundle` and diff task-level costs against 6154.
risk: low
rule_status: public_source
repro_status: imported
diff_status: not_started
priority: P0
assigned_exp_id: GOLF_20260607_002_public_6029_diff

## SRC_KAGGLE_NOTEBOOK_AFR1STE_5689

source_id: SRC_KAGGLE_NOTEBOOK_AFR1STE_5689
source_type: notebook
title: NeuroGolf 5689.51 Current Rules Open Solution
author_or_team: Afr1ste
url_or_identifier: https://www.kaggle.com/code/afr1ste/neurogolf-5689-51-current-rules-open-solution
date_accessed: 2026-06-07
claimed_score: 5689.51
tasks_mentioned: all
idea_summary: Public open artifact and earlier strong baseline.
implementation_hint: Use as provenance for lower-score fallback and task-level swaps.
risk: low
rule_status: public_source
repro_status: imported
priority: P1
assigned_exp_id:

## SRC_KAGGLE_NOTEBOOK_BEICICC_6645

source_id: SRC_KAGGLE_NOTEBOOK_BEICICC_6645
source_type: notebook
title: NeuroGolf 6645.39 Public Score Open Solution
author_or_team: Kun Zhang
url_or_identifier: https://www.kaggle.com/code/beicicc/neurogolf-6645-39-public-score-open-solution
date_accessed: 2026-06-07
claimed_score: 6645.39
tasks_mentioned: all
idea_summary: Public full-bundle open solution shipped as a reusable submission artifact with compact per-task ONNX graphs.
implementation_hint: Normalize the artifact bundle to task001-task400 and use it as the first high-upside full-replace baseline.
risk: low
rule_status: public_source
repro_status: imported
priority: P0
assigned_exp_id: GOLF_20260607_004_public_notebook_full_replace

## SRC_KAGGLE_NOTEBOOK_VYANKTESH_MULTI_SOURCE

source_id: SRC_KAGGLE_NOTEBOOK_VYANKTESH_MULTI_SOURCE
source_type: notebook
title: NeuroGolf Multi-Source ONNX Solver
author_or_team: zorojuro
url_or_identifier: https://www.kaggle.com/code/vyankteshdwivedi/neurogolf-multi-source-onnx-solver
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: all
idea_summary: Public multi-source blended ONNX bundle likely useful for top-k task harvest and alternative full-replace fallback.
implementation_hint: Diff against 6154 and 6645; harvest per-task wins after validating the imported artifact.
risk: low
rule_status: public_source
repro_status: imported
priority: P1
assigned_exp_id:

## SRC_KAGGLE_NOTEBOOK_GLM_OPUS_COST_OPT

source_id: SRC_KAGGLE_NOTEBOOK_GLM_OPUS_COST_OPT
source_type: notebook
title: GLM vs Opus: ONNX cost-opt (NeuroGolf 2026)
author_or_team: Chet
url_or_identifier: https://www.kaggle.com/code/jsrdcht/glm-vs-opus-onnx-cost-opt-neurogolf-2026
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: unknown
idea_summary: Public cost-optimization comparison likely useful for rewrite lane.
implementation_hint: Import next, extract operator rewrite motifs and changed tasks.
risk: low
rule_status: public_source
repro_status: not_started
priority: P1
assigned_exp_id:

## SRC_DISCUSSION_BOTTOM15_TASKS

source_id: SRC_DISCUSSION_BOTTOM15_TASKS
source_type: discussion
title: My current bottom 15 NeuroGolf Tasks - Any Ideas?
author_or_team: Tony Li
url_or_identifier: https://www.kaggle.com/competitions/neurogolf-2026/discussion/704006
date_accessed: 2026-06-07
claimed_score: per-task tail scores listed
tasks_mentioned: 158,233,173,054,025,285,366,133,286,255,349,018,187,145,243
idea_summary: High-value task list for single-task override and low-score tail improvements.
implementation_hint: Prioritize these task IDs after first submission.
risk: low
rule_status: public_discussion
repro_status: not_started
priority: P0
assigned_exp_id:

## SRC_DISCUSSION_CORRIDOR_ONNX_PATTERNS

source_id: SRC_DISCUSSION_CORRIDOR_ONNX_PATTERNS
source_type: discussion
title: Compact ONNX patterns for dynamic corridor / empty-rectangle fill?
author_or_team: Xu Jinghang111
url_or_identifier: https://www.kaggle.com/competitions/neurogolf-2026/discussion/704769
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: corridor and empty-rectangle family
idea_summary: ReduceSum, MaxPool-style morphology, and Where fills as low-node patterns.
implementation_hint: Convert into ONNX rewrite playbook examples.
risk: low
rule_status: public_discussion
repro_status: not_started
priority: P1
assigned_exp_id:

## SRC_DISCUSSION_SUBMISSION_LIMIT_REENABLED

source_id: SRC_DISCUSSION_SUBMISSION_LIMIT_REENABLED
source_type: discussion
title: Submissions amount re-enabled
author_or_team: Ashley Oldacre
url_or_identifier: https://www.kaggle.com/competitions/neurogolf-2026/discussion/703112
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: all
idea_summary: Repo evidence records a host-note claim that submissions were reset to allow 100 per day, but this is not visible in the formal rules snapshot stored under `competition_pages.json`.
implementation_hint: Treat this as a secondary claim; confirm live quota from Kaggle UI or CLI-visible behavior before batch submits.
risk: low
rule_status: public_host_discussion
repro_status: imported
priority: P0
assigned_exp_id:

## SRC_ARC_GEN_GITHUB

source_id: SRC_ARC_GEN_GITHUB
source_type: github
title: google/ARC-GEN
author_or_team: Google
url_or_identifier: https://github.com/google/arc-gen
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: all ARC-AGI-1 tasks
idea_summary: Procedural benchmark generator used in NeuroGolf and 2025 Google Code Golf.
implementation_hint: Add adapter for extra per-task validation and synthesis data.
risk: low
rule_status: public_github
repro_status: not_started
priority: P0
assigned_exp_id:

## SRC_ARC_GEN_100K_DATASET

source_id: SRC_ARC_GEN_100K_DATASET
source_type: dataset
title: The ARC-GEN-100K Dataset
author_or_team: ARC-GEN authors
url_or_identifier: https://www.kaggle.com/datasets/arcgen100k/the-arc-gen-100k-dataset
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: all ARC-AGI-1 training tasks
idea_summary: 100,000 ARC-GEN example pairs covering all 400 ARC-AGI-1 training tasks.
implementation_hint: Use for enhanced validation before submitting task overrides.
risk: low
rule_status: public_dataset
repro_status: not_started
priority: P1
assigned_exp_id:

## SRC_RE_ARC_GITHUB

source_id: SRC_RE_ARC_GITHUB
source_type: github
title: michaelhodel/re-arc
author_or_team: Michael Hodel
url_or_identifier: https://github.com/michaelhodel/re-arc
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: 400 ARC training tasks
idea_summary: Procedural generators and verified generated examples for all 400 ARC training tasks.
implementation_hint: Use as independent validation/generator reference; maps well to task bank.
risk: low
rule_status: public_github_mit
repro_status: not_started
priority: P1
assigned_exp_id:

## SRC_ARC_DSL_GITHUB

source_id: SRC_ARC_DSL_GITHUB
source_type: github
title: michaelhodel/arc-dsl
author_or_team: Michael Hodel
url_or_identifier: https://github.com/michaelhodel/arc-dsl
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: ARC training tasks
idea_summary: DSL primitives and solver programs for ARC tasks.
implementation_hint: Translate selected DSL primitives into small ONNX graph templates.
risk: low
rule_status: public_github_mit
repro_status: not_started
priority: P1
assigned_exp_id:

## SRC_ARC_PRIZE_2024_REPORT

source_id: SRC_ARC_PRIZE_2024_REPORT
source_type: paper
title: ARC Prize 2024 Technical Report
author_or_team: Chollet, Knoop, Kamradt, Landers
url_or_identifier: https://arcprize.org/media/arc-prize-2024-technical-report.pdf
date_accessed: 2026-06-07
claimed_score: ARC-AGI private SOTA increased to 55.5 percent
tasks_mentioned: ARC-AGI
idea_summary: Surveys deep-learning-guided program synthesis and test-time training patterns.
implementation_hint: Mine program synthesis and validation workflow ideas, not direct ONNX.
risk: low
rule_status: public_paper
repro_status: not_started
priority: P2
assigned_exp_id:

## SRC_GOOGLE_CODE_GOLF_2025

source_id: SRC_GOOGLE_CODE_GOLF_2025
source_type: writeup
title: NeurIPS 2025 - Google Code Golf Championship
author_or_team: Google DeepMind / Kaggle community
url_or_identifier: https://www.kaggle.com/competitions/google-code-golf-2025
date_accessed: 2026-06-07
claimed_score:
tasks_mentioned: 400 ARC-AGI tasks
idea_summary: Prior ARC code-golf competition; useful for per-task solution strategy and ARC-GEN usage.
implementation_hint: Review public writeups for task decomposition and reusable rule families.
risk: low
rule_status: public_competition
repro_status: not_started
priority: P1
assigned_exp_id:

## SRC_KAGGLE_NOTEBOOK_MIRZA_BEST_SCORE

source_id: SRC_KAGGLE_NOTEBOOK_MIRZA_BEST_SCORE
source_type: notebook
title: Best Score NeuroGolf Championship NoteBook
author_or_team: Mirza Yasir Abdullah Baig
url_or_identifier: https://www.kaggle.com/code/mirzayasirabdullah07/best-score-neurogolf-championship-notebook
date_accessed: 2026-06-08
claimed_score:
tasks_mentioned: all
idea_summary: Fresh high-vote public notebook discovered after the 6154 baseline; likely blend or public-artifact aggregation source.
implementation_hint: Import notebook output next, validate structure, then use as full-replace and task-level diff source.
risk: medium
rule_status: public_source
repro_status: not_started
priority: P0
assigned_exp_id:

## SRC_KAGGLE_NOTEBOOK_BIOHACK_SUPER_BLEND

source_id: SRC_KAGGLE_NOTEBOOK_BIOHACK_SUPER_BLEND
source_type: notebook
title: Neurogolf Super Blend:Best Public Score
author_or_team: Emre Cirak
url_or_identifier: https://www.kaggle.com/code/biohack44/neurogolf-super-blend-best-public-score
date_accessed: 2026-06-08
claimed_score:
tasks_mentioned: all
idea_summary: Public super-blend notebook found by Kaggle Code search; high-value source for full-bundle replacement and per-task harvesting.
implementation_hint: Download output, normalize task files, reject if structural rules fail, otherwise submit as a full-replace probe.
risk: medium
rule_status: public_source
repro_status: not_started
priority: P0
assigned_exp_id:

## SRC_KAGGLE_NOTEBOOK_SEDDIK_SURGICAL_ONNX

source_id: SRC_KAGGLE_NOTEBOOK_SEDDIK_SURGICAL_ONNX
source_type: notebook
title: Surgical ONNX: Precision Parameter Reduction
author_or_team: seddik turki
url_or_identifier: https://www.kaggle.com/code/seddiktrk/surgical-onnx-precision-parameter-reduction
date_accessed: 2026-06-08
claimed_score:
tasks_mentioned: unknown
idea_summary: Public ONNX surgery notebook focused on precision and parameter reduction; candidate source for memory-footprint rewrite lane.
implementation_hint: Extract rewrite motifs only after checking they reduce memory footprint, not only zip size or parameter count.
risk: medium
rule_status: public_source
repro_status: not_started
priority: P1
assigned_exp_id:

## SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX

source_id: SRC_KAGGLE_NOTEBOOK_JONATHAN_CONSTRAINT_MIX
source_type: notebook
title: [NGC26] Constraint Smart Logic Mix Blending
author_or_team: Jonathan Chan
url_or_identifier: https://www.kaggle.com/code/jonathanchan/ngc26-constraint-smart-logic-mix-blending
date_accessed: 2026-06-08
claimed_score:
tasks_mentioned: all
idea_summary: High-vote public logic/blending notebook; likely useful for task-level selection and rule-family alternatives.
implementation_hint: Import output, diff task-level models against 6154 and 6645, then submit a small aggressive mix.
risk: medium
rule_status: public_source
repro_status: not_started
priority: P1
assigned_exp_id:

## SRC_KAGGLE_NOTEBOOK_KOJIMAR_6272_AUDITED_OVERRIDES

source_id: SRC_KAGGLE_NOTEBOOK_KOJIMAR_6272_AUDITED_OVERRIDES
source_type: notebook
title: [6272.50 LB] Audited NeuroGolf ONNX Overrides
author_or_team: islet / kojimar
url_or_identifier: https://www.kaggle.com/code/kojimar/6272-50-lb-audited-neurogolf-onnx-overrides
date_accessed: 2026-06-08
claimed_score: 6272.50
tasks_mentioned: all; base_submission plus 300 override ONNX tasks
idea_summary: Fresh public high-score audited override notebook. Companion dataset kojimar/neurogolf-6272-50-minimal-onnx-assets-v1 provides 400 base ONNX files and 300 overrides, enabling full bundle reproduction and task-level harvest.
implementation_hint: Rebuild submission by overlaying overrides on base_submission; validate full bundle first, then harvest individual override tasks and targeted probes.
risk: medium
rule_status: public_notebook_and_cc0_dataset
repro_status: reproducing
priority: P0
assigned_exp_id: GOLF_20260608_025_kojimar_6272_full_replace

## SRC_KAGGLE_NOTEBOOK_BIOHACK_BEST_BLEND_MAX_PUBLIC

source_id: SRC_KAGGLE_NOTEBOOK_BIOHACK_BEST_BLEND_MAX_PUBLIC
source_type: notebook
title: Neurogolf: Best Blend Max Public Score
author_or_team: Emre Cirak / biohack44
url_or_identifier: https://www.kaggle.com/code/biohack44/neurogolf-best-blend-max-public-score
date_accessed: 2026-06-09
claimed_score:
tasks_mentioned: all
idea_summary: Public per-task max blend notebook that scores two existing submissions through the official scorer and keeps the locally correct lower-cost task model. The notebook output audit reports 400 tasks, 0 incorrect, 0 other problems, and local total 6258.50.
implementation_hint: Pull notebook output, filter task001-task400 from the output directory, validate locally, then submit as a full-bundle replacement or harvest source.
risk: medium
rule_status: public_notebook_output
repro_status: reproducing
priority: P0
assigned_exp_id: GOLF_20260608_032_biohack_best_blend_max_full

## SRC_KAGGLE_NOTEBOOK_MASSIMILIANO_CONV_PART4

source_id: SRC_KAGGLE_NOTEBOOK_MASSIMILIANO_CONV_PART4
source_type: notebook
title: Convolution Series - Part 4
author_or_team: MassimilianoGhiotto
url_or_identifier: https://www.kaggle.com/code/massimilianoghiotto/convolution-series-part-4
date_accessed: 2026-06-09
claimed_score:
tasks_mentioned: task258; submission bundle
idea_summary: Public ONNX convolution tutorial for NeuroGolf task258. It demonstrates replacing a dense 10x10 color interaction convolution with grouped convolution to reduce parameters while preserving the ARC transformation.
implementation_hint: Use task258_optimized.onnx as a targeted operator-family replacement probe against the current best bundle; avoid duplicate full submission because the notebook submission.zip matches an already tested 6255 source family.
risk: low
rule_status: public_notebook_output
repro_status: reproducing
priority: P1
assigned_exp_id: GOLF_20260608_033_massimiliano_task258_groupconv_probe

## SRC_HF_ROGERMT_6273_SUBMISSION

source_id: SRC_HF_ROGERMT_6273_SUBMISSION
source_type: dataset
title: rogermt/neurogolf-solver submission-6273.zip
author_or_team: Roger Martinez / rogermt
url_or_identifier: https://huggingface.co/rogermt/neurogolf-solver
date_accessed: 2026-06-09
claimed_score: 6273 public-family artifact
tasks_mentioned: all
idea_summary: Public Hugging Face repository containing multiple NeuroGolf submission bundles, optimized medal-solvers, and task-level solver notes. The `submission-6273.zip` artifact is the strongest currently available public open repository bundle found in the 6276-source search pass.
implementation_hint: Validate the 400-task bundle as a full replacement first. If public score does not improve current best, harvest the optimized `medal-solvers/optimized/task*.onnx` files as targeted task probes.
risk: medium
rule_status: public_open_repository_artifact
repro_status: reproducing
priority: P0
assigned_exp_id: GOLF_20260608_034_rogermt_6273_full_replace
