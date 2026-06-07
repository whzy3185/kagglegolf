# Session Report

Last updated: 2026-06-07T20:54:45

## Workspace

- Current directory: E:\Jitter\kagglegolf
- Current branch: main
- Competition: neurogolf-2026

## Data and Rules

- Official data manifest: data/manifests/official_files_manifest.json
- Task inventory: data/manifests/task_inventory.csv
- Rules summary: reports/RULES_SUMMARY.md

## Candidate

- exp_id: GOLF_20260607_001_public_6154_repro
- candidate path: submissions/candidates/GOLF_20260607_001_public_6154_repro
- submission path: submissions/candidates/GOLF_20260607_001_public_6154_repro/submission.zip
- notebook path: notebooks/kaggle_submit_current.ipynb
- source: SRC_KAGGLE_NOTEBOOK_OCTAVIO_6154
- package sha256: 7334efaa771c61cda51a73772d8b29370edd0663fc40a9eafddb1d85f63e7f6d
- local validation ok: True
- examples checked: 1200
- examples failed: 0
- Kaggle dataset input: muelsyse111/neurogolf-current-candidate
- Kaggle Notebook: https://www.kaggle.com/code/muelsyse111/neurogolf-submit-current
- Notebook output: notebooks/output/submission.zip
- Notebook output ONNX content match: true, 400/400 files identical by SHA256
- Kaggle submission id: 53450566
- Kaggle submission status: COMPLETE
- Kaggle public score: 6154.71

## Kaggle Submission History

```text
ref       fileName        date                        description                                                                                                                              status                    publicScore
53450566  submission.zip  2026-06-07 12:27:16.493000  GOLF_20260607_001_public_6154_repro | public 6154 baseline closure | source=SRC_KAGGLE_NOTEBOOK_OCTAVIO_6154 | changed=all | local=pass  SubmissionStatus.COMPLETE  6154.71

```

## Notes

Kaggle CLI supports direct Notebook-output submission with `kaggle competitions submit neurogolf-2026 -k <kernel> -v <version> -f submission.zip -m <message>`. Earlier manual-submit-only notes are obsolete.
