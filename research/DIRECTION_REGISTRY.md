# Direction Registry

## DIR_20260608_001_public_highscore_harvest

direction_id: DIR_20260608_001_public_highscore_harvest
status: active
created_at: 2026-06-08
target_exp_ids:
  - GOLF_20260607_001_public_6154_repro
  - GOLF_20260608_005_mirza_full_replace
  - GOLF_20260608_005_mirza_structural_pass_mix
  - GOLF_20260608_006_biohack_super_blend_full_replace
  - GOLF_20260608_006_biohack_super_blend_structural_pass_mix
  - GOLF_20260608_008_jonathan_constraint_logic_mix
  - GOLF_20260608_008b_jonathan_structural_pass_mix
  - GOLF_20260608_016_jonathan_task233_probe
  - GOLF_20260608_016_jonathan_task255_probe
  - GOLF_20260608_017_jonathan_task286_probe
  - GOLF_20260608_018_jonathan_task173_probe
  - GOLF_20260608_019_jonathan_top5_mix_probe
  - GOLF_20260608_020_beicicc_task366_probe
  - GOLF_20260608_021_jsrdcht_memory_task255_probe
  - GOLF_20260608_022_jonathan_task285_probe
  - GOLF_20260608_023_beicicc_task076_probe
  - GOLF_20260608_024_jsrdcht_memory_task285_probe
  - GOLF_20260608_025_kojimar_6272_full_replace
  - GOLF_20260608_026_kojimar_6272_override_probe_mix
  - GOLF_20260608_014_biohack_task187_probe
  - GOLF_20260608_012_mirza_task187_probe
  - GOLF_20260608_026_beicicc_task169_probe
  - GOLF_20260608_027_jsrdcht_memory_task018_probe
  - GOLF_20260608_028_jonathan_task025_probe

hypothesis:
  Current best 6154.71 is too far from the 7000 target. High-score public notebooks may contain stronger full bundles or task-level ONNX variants that can close the gap faster than local micro-optimization.

leaderboard_basis:
  source_id: SRC_KAGGLE_NOTEBOOK_MIRZA_BEST_SCORE
  reason: Fresh P0 public high-score notebook discovered from the current NeuroGolf public notebook ecosystem.

paper_basis:
  source_id: SRC_ARC_PRIZE_2024_REPORT
  reason: ARC Prize technical report supports program-synthesis and task-level search as more relevant than monolithic model training for ARC-style tasks.

open_repo_basis:
  source_id: SRC_ARC_GEN_GITHUB
  reason: ARC-GEN provides procedural data generation and validation strategy for ARC-style tasks.

historical_competition_basis:
  source_id: SRC_GOOGLE_CODE_GOLF_2025
  reason: Prior ARC code-golf competition supports task-level harvesting and compression as central strategy.

implementation_plan:
  - import public notebook output
  - validate full bundle
  - submit if structural pass
  - if full bundle fails, harvest structural-pass tasks
  - diff against current best and submit aggressive mixes

risk:
  - public-source overfit
  - hidden private mismatch
  - structural validation failure

rollback_rule:
  If public score decreases, keep source as alternate task pool but do not overwrite normal best_by_task.

success_criteria:
  At least one validator-pass public-source candidate receives Kaggle score feedback.

## DIR_20260608_002_bottom15_task_override

direction_id: DIR_20260608_002_bottom15_task_override
status: active
created_at: 2026-06-08
target_exp_ids:
  - GOLF_20260607_002_public_6029_aggressive_mix
  - GOLF_20260607_003_bottom15_single_task_probe
  - GOLF_20260608_010_bottom15_public_best_mix

hypothesis:
  Bottom-tail tasks have disproportionate upside. Single-task probes can identify whether public-source alternatives improve leaderboard score before broad mixing.

leaderboard_basis:
  source_id: SRC_DISCUSSION_BOTTOM15_TASKS
  reason: Current NeuroGolf discussion identifies a concrete bottom-15 task list for high-value tail improvement.

paper_basis:
  source_id: SRC_ARC_PRIZE_2024_REPORT
  reason: ARC task-level reasoning and program-synthesis results support targeted per-task intervention.

open_repo_basis:
  source_id: SRC_RE_ARC_GITHUB
  reason: RE-ARC provides independent task generators and validation references for ARC training tasks.

historical_competition_basis:
  source_id: SRC_GOOGLE_CODE_GOLF_2025
  reason: Prior ARC code-golf setting emphasizes individual task compression and task-specific solving.

implementation_plan:
  - prioritize tasks 158,233,173,054,025,285,366,133,286,255,349,018,187,145,243
  - submit single-task probes
  - record task-level delta
  - only promote confirmed or suspected wins into later mixes

risk:
  - single public LB signal may be noisy
  - broad mix may obscure task-level attribution
  - high-risk task replacements may worsen memory footprint

rollback_rule:
  High-risk task wins go to high-risk bank first, not normal best_by_task.

success_criteria:
  At least one bottom15 single-task or small-mix submission receives Kaggle feedback.

## DIR_20260608_003_memory_first_onnx_surgery

direction_id: DIR_20260608_003_memory_first_onnx_surgery
status: active
created_at: 2026-06-08
target_exp_ids:
  - GOLF_20260608_011_memory_surgery_top_cost_mix
  - GOLF_20260608_029_seddik_surgery_6272

hypothesis:
  NeuroGolf scoring is strongly affected by memory footprint and graph cost. Structural ONNX rewrites can improve high-tail tasks when public bundles do not provide direct wins.

leaderboard_basis:
  source_id: SRC_KAGGLE_NOTEBOOK_SEDDIK_SURGICAL_ONNX
  reason: Public notebook explicitly targets ONNX precision and parameter reduction and is relevant to the memory-surgery lane.

paper_basis:
  source_id: SRC_ARC_PRIZE_2024_REPORT
  reason: Technical report motivates task-specific reasoning pipelines and validation-based search.

open_repo_basis:
  source_id: SRC_ARC_DSL_GITHUB
  reason: ARC-DSL provides compositional primitives that can be translated into compact ONNX graph patterns.

historical_competition_basis:
  source_id: SRC_GOOGLE_CODE_GOLF_2025
  reason: Prior ARC code-golf competition supports aggressive task-specific compression.

implementation_plan:
  - profile high-memory tasks
  - apply structural graph rewrites only
  - validate before and after
  - submit if validator passes and candidate differs from current best

risk:
  - scorer proxy may not match official utility
  - rewrite may break hidden behavior
  - local examples may be insufficient

rollback_rule:
  Failed surgery candidates remain as pattern evidence but do not update task bank.

success_criteria:
  Produce at least one validator-pass memory-surgery candidate with before/after profile.

## DIR_20260608_004_beicicc_structural_normalization

direction_id: DIR_20260608_004_beicicc_structural_normalization
status: active
created_at: 2026-06-08
target_exp_ids:
  - GOLF_20260607_004_public_notebook_full_replace
  - GOLF_20260608_004b_beicicc_structural_pass_mix
  - GOLF_20260608_004c_beicicc_domain_normalized_mix
  - GOLF_20260608_030_beicicc_inline_full
  - GOLF_20260608_031_beicicc_inline_396_mix

hypothesis:
  Beicicc 6645 public solution has stronger leaderboard score than the current 6154 baseline, but its raw artifact fails local structural validation due to nonstandard ONNX domains/functions. Structural-pass task harvesting or safe normalization may recover usable high-score components.

leaderboard_basis:
  source_id: SRC_KAGGLE_NOTEBOOK_BEICICC_6645
  reason: Public notebook claims 6645.39, which is higher than current 6154.71.

paper_basis:
  source_id: SRC_ARC_PRIZE_2024_REPORT
  reason: ARC technical report supports programmatic task-level solution discovery and validation.

open_repo_basis:
  source_id: SRC_ARC_GEN_GITHUB
  reason: ARC-GEN can provide additional validation for normalized or harvested task variants.

historical_competition_basis:
  source_id: SRC_GOOGLE_CODE_GOLF_2025
  reason: Prior code-golf competition supports reuse and compression of task-specific artifacts.

implementation_plan:
  - reject raw full-replace 004
  - extract structural-pass tasks only
  - attempt safe function inline and domain normalization
  - validate again
  - submit 004b or 004c only if structural pass

risk:
  - bad_opset_domain:golf
  - has_functions
  - normalization may alter behavior
  - full raw artifact is not directly submittable

rollback_rule:
  Never submit the original failed 004. Only submit normalized or structural-pass candidates.

success_criteria:
  Generate a validator-pass Beicicc-derived mix or a clear rejection report.
