# Local Recap Upload Audit

last_updated: 2026-07-18
local_repo: `E:\kagglegolf`
remote: `git@github.com:whzy3185/kagglegolf.git`
branch: `main`
latest_checked_commit_before_doc_sync: `274b103 Add live NeuroGolf task dashboard`

## Summary

The core high-score recap files found locally are tracked in `kagglegolf`. The branch was not ahead of `origin/main` before this documentation sync, but the working tree contains many generated state updates and submission logs. This audit does not promote raw ONNX, raw data, submission ZIPs, or credential-bearing files.

## Tracked Recap Files Confirmed Locally

These paths are tracked by Git in `kagglegolf`:

- `reports/PRVSIYAN_7266_72_REPRO_20260709.md`
- `reports/PUBLIC_7015_FORK_REPORT.md`
- `reports/PUBLIC_7113_FORK_REPORT.md`
- `reports/ONNX_VISUALIZATION_DASHBOARD_20260709.md`
- `data/public_neurogolf_intel/reports/HIGH_SCORE_SOURCE_AUDIT.md`
- `research/EVIDENCE_REGISTRY.md`
- `research/LEADERBOARD_INTEL.md`
- `research/DISCUSSION_NOTES.md`
- `research/PUBLIC_NOTEBOOKS.md`
- `research/PUBLIC_REPOS.md`
- `research/HISTORICAL_WRITEUPS.md`
- `task_bank/public_fork_7015_task_bank.csv`
- `task_bank/public_fork_7113_task_bank.csv`
- `task_bank/simple_exact_task_bank.csv`
- `task_bank/simple_exact_batch_results.csv`

## New Recap Files Added by This Sync

- `research/FIRST_PLACE_CONTACT_AND_SLACK_COLLAB.md`
- `reports/HIGH_SCORE_SOLUTION_RETROSPECTIVE.md`
- `reports/LOCAL_RECAP_UPLOAD_AUDIT.md`

The same synthesized retrospective set is also copied to `E:\kaggleneurogolf-2026\retrospectives\neurogolf-2026\`.

## Current Dirty-Tree Caveat

Before this documentation sync, the local `kagglegolf` worktree already had modified generated reports, queue CSVs, manifests, task-bank CSVs, notebook files, and many untracked submission/kernel logs. Those files are operational state, not all of them are curated retrospectives. They should be committed only after checking that they do not include:

- raw competition data;
- raw ONNX directories;
- `submission.zip` or large output bundles;
- Kaggle/Hugging Face tokens;
- private local paths that reveal credentials;
- generated duplicate logs with no analytical value.

## Not Uploaded Intentionally

- `data/raw/`
- `data/interim/` extracted artifacts unless separately curated;
- `submissions/candidates/*/onnx/`;
- `submissions/candidates/*/submission.zip`;
- Kaggle or Hugging Face credential files;
- local notebook output payloads that are better stored as Kaggle outputs or ignored artifacts.

## External Verification Notes

- `kaggle competitions leaderboard -c neurogolf-2026 --show 50` returned `403 Forbidden` in this local environment.
- Public source links and local cached Kaggle topic/notebook records were used for the retrospective.
- A fresh live leaderboard/rank audit still requires Kaggle UI access or a Kaggle account whose API can read the leaderboard endpoint.
