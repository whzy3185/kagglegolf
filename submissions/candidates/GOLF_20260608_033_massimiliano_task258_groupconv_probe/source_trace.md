# GOLF_20260608_033_massimiliano_task258_groupconv_probe Source Trace

direction_id: DIR_20260608_003_memory_first_onnx_surgery
primary_source_id: SRC_KAGGLE_NOTEBOOK_MASSIMILIANO_CONV_PART4

leaderboard_basis:
  source_id: SRC_KAGGLE_NOTEBOOK_MASSIMILIANO_CONV_PART4
  reason: Candidate-specific leaderboard evidence. Direction rationale: Public notebook explicitly targets ONNX precision and parameter reduction and is relevant to the memory-surgery lane.

paper_basis:
  source_id: SRC_ARC_PRIZE_2024_REPORT
  reason: Technical report motivates task-specific reasoning pipelines and validation-based search.

open_repo_basis:
  source_id: SRC_ARC_DSL_GITHUB
  reason: ARC-DSL provides compositional primitives that can be translated into compact ONNX graph patterns.

historical_competition_basis:
  source_id: SRC_GOOGLE_CODE_GOLF_2025
  reason: Prior ARC code-golf competition supports aggressive task-specific compression.

changed_tasks: task258
parent_exp_id: GOLF_20260607_001_public_6154_repro
