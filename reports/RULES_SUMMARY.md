# Rules Summary

Last updated: 2026-06-09

## Official Files

- `neurogolf_utils/neurogolf_utils.py`
- `task001.json` through `task400.json`
- No official sample submission file was found in the downloaded zip.

## Task Format

Each task JSON has `train`, `test`, and `arc-gen` lists. Each pair has `input` and `output` grids.
Grid cells are integers 0 through 9. Official pages state grid sizes range from 1x1 to 30x30, while the official utility ignores examples larger than 30x30 during validation.

## Tensor Contract

- Input name: `input`
- Output name: `output`
- Shape: `[1, 10, 30, 30]`
- Encoding: one-hot color channels, zero-hot outside the original grid border.
- Dtype: float32, per official `neurogolf_utils.py`.
- Opset: 10, per official `neurogolf_utils.py`.
- IR version: 10, per official `neurogolf_utils.py`.

## Submission Package

Submit `submission.zip` containing at most one ONNX file per task:

```text
task001.onnx
task002.onnx
...
task400.onnx
```

## ONNX Constraints

- Statically defined tensor and parameter shapes are required.
- One input and one output are required by the official utility.
- File size limit per ONNX: 1.44 MB.
- Banned ops from current official utility/page: `Loop`, `Scan`, `NonZero`, `Unique`, `Script`, `Function`, `Compress`.
- Custom domains, functions, subgraphs, duplicate value_info names, name collisions, sequences, nonpositive dimensions, and unsafe tensor names are rejected by the official utility.

## Scoring

For each functionally correct task network:

```text
max(1, 25 - ln(cost))
cost = memory_footprint_bytes + parameter_count
```

MACs do not contribute under the current utility changelog.

The host's May 4 update explicitly removed MACs after profiler issues. Current optimization order is:

1. functional correctness;
2. cumulative runtime memory footprint;
3. parameter count.

Constant tensor values contribute to parameter count. Tensor dimensions must be positive and statically known after shape inference, using shapes verified by the official ONNX Runtime.

## Pinned Runtime

The host-published compatibility stack is:

```text
numpy==2.4.4
onnx==1.21.0
onnxruntime==1.24.4
onnx-tool==1.0.1
```

## Public/Private Validation

Correctness is checked against ARC-AGI public training v1 task examples plus a small private benchmark suite to discourage overfitting.

## External Sources

The rules page permits public external data/tools/models when reasonably accessible and rule-compliant. Private leaks, hidden answer reconstruction, and untraceable sources are forbidden by project policy.

## Final Submission Rule

The original rules snapshot stated five submissions per day and up to two final submissions for judging.

Current effective quota:

- Kaggle staff topic `703112`, posted 2026-05-28, states that the competition was reset to allow 100 submissions per day.
- Live competition metadata also reports `max_daily_submissions=100`.
- Project policy therefore uses 100/day as the current platform quota and records any platform rejection directly.

## Raw Page Snapshots

Page snapshots are stored in `data/manifests/competition_pages.json`.
