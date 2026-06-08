# High Risk Register

High-risk candidates are allowed only when they remain inside competition rules and pass local validation.

Fields:
risk_id, source_id, hypothesis, rule_basis, why_high_risk, candidate_exp_id, tasks_affected, local_validator_result, submission_result, possible_rule_change, rollback_plan

## HR_20260608_001_6029_BOTTOM15_MIX

risk_id: HR_20260608_001_6029_BOTTOM15_MIX
source_id: SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029
hypothesis: 6029 bundle may contain local tail-task improvements even when overall bundle is lower than 6154.
rule_basis: Public Kaggle notebook source; candidate passed local structural and example validation before submission.
why_high_risk: Source bundle is lower-scoring overall and task-level marginal contribution is uncertain.
candidate_exp_id: GOLF_20260607_002_public_6029_aggressive_mix
tasks_affected: task286,task173,task054
local_validator_result: pass
submission_result: 53472165 / public 6154.59 / delta -0.12
possible_rule_change: none expected; ordinary public-source override.
rollback_plan: Do not merge into normal best_by_task; keep only as negative boundary evidence.

## HR_20260608_002_6029_TASK286_SINGLE

risk_id: HR_20260608_002_6029_TASK286_SINGLE
source_id: SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029
hypothesis: task286 from 6029 could improve the bottom-15 tail as an isolated override.
rule_basis: Public Kaggle notebook source; single-task candidate passed local structural and example validation before submission.
why_high_risk: Single-task public LB attribution is noisy and the source bundle is lower-scoring overall.
candidate_exp_id: GOLF_20260607_003_bottom15_single_task_probe
tasks_affected: task286
local_validator_result: pass
submission_result: 53472175 / public 6154.67 / delta -0.04
possible_rule_change: none expected; ordinary public-source override.
rollback_plan: Do not merge task286 into normal best_by_task; keep as alternate-source evidence.
