# Notebook Output Status

Queue source: `experiments/notebook_queue.csv`

Line N owns notebook output production and verification. Line S owns competition submission and score recording.

## 2026-06-08 submission-line finding

- GOLF_20260607_002_public_6029_aggressive_mix pushed to `muelsyse111/neurogolf-submit-current` as version 5, but sidecar `submission_source.zip` was not available to the Kaggle runtime.
- Dataset-based version 4 also failed because `/kaggle/input/neurogolf-manual-rewrites-v205` did not expose `task001.onnx` to the runtime.
- For immediate feedback, 002 and 003 were submitted with local zip fallback and marked high-risk/non-best until scores returned.
- Next Notebook-output fix should use a Kaggle dataset artifact for candidate payloads or an existing public dataset source that is verified inside runtime before `competitions submit -k`.
