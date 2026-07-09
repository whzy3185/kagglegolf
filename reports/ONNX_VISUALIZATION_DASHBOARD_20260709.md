# ONNX Visualization Dashboard

Date: 2026-07-09

## Kaggle Discussion Evidence

Queried with Kaggle CLI:

```powershell
kaggle competitions topics show neurogolf-2026 699313 --format json --page-size 200
kaggle competitions topics show neurogolf-2026 699429 --format json --page-size 200
```

Confirmed public discussion leads:

- `699313`: **Web GUI to Build ONNX by Hand**, Chris Deotte. The thread discusses a GUI for hand-building ONNX solutions and links to the open-source GUI thread.
- `699429`: **Web GUI for Hand Solving Tasks Open Source**, Clark Kitchen. The thread discusses an open-source hand-solving GUI.
- A `699429` comment flags the `/api/export` Hugging Face upload path and warns that `HF_REPO_ID` must point to the user's own repository. The author replied that owner verification was added before export.

## Local Deployment

The repository now has a read-only live dashboard path that does not require Kaggle or Hugging Face credentials:

```powershell
python scripts/neurogolf/04_render_dashboard.py
python scripts/neurogolf/06_serve_dashboard.py --port 8765
```

Open:

```text
http://127.0.0.1:8765/task_scoreboard.html
```

The HTML refreshes every 30 seconds. To keep data updating while editing a submission directory or zip:

```powershell
python scripts/neurogolf/05_watch_and_refresh.py --input <submission_dir_or_zip> --candidate-id <candidate_id> --interval 30
```

## Current Refresh

The full task table was refreshed from the reproduced `prvsiyan` public artifact:

- candidate: `GOLF_20260709_101_prvsiyan_7266_72_repro`
- public score: 7266.72
- local task-table total: 7266.585992
- pass/fail/missing: 400/0/0

The dashboard files live under:

```text
data/neurogolf_task_table/
```

## Workplace C Export

The owner-specific export script is:

```powershell
python scripts/neurogolf/07_export_owner_dashboard.py --owner C --assignment-csv E:\kongming\NGC-work\assignments\task_assignment_400.csv --out-dir E:\kongming\NGC-work\workplace_C\dashboard
```

It writes a read-only C task dashboard without ONNX files, submission zips, raw data, tokens, or upload endpoints.
