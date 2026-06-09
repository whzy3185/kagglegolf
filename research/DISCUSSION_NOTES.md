# Discussion Notes

Refreshed on 2026-06-09 from the public NeuroGolf forum.

## Official Scorer State

- `696953`, host update on 2026-05-04: MACs were removed from the objective. Cost is determined by cumulative memory footprint and parameter count. Positive dimensions and ONNX Runtime-verified shapes are enforced.
- `695230`, host update on 2026-04-28: constant values count toward parameters, static shapes are required after shape inference, custom domains/functions/subgraphs are rejected, and `Compress` joined the excluded operator list.
- `693088`, host compatibility response: pinned stack is `numpy==2.4.4`, `onnx==1.21.0`, `onnxruntime==1.24.4`, `onnx-tool==1.0.1`.
- `703112`, Kaggle staff: the live competition was reset to allow 100 submissions per day. This supersedes the original 5/day snapshot.

## High-Rank Workflow Evidence

- `703914`, Andrey Yunoshev (~6580 when posted):
  - Maintain per-task dossiers, full attempt history, per-node memory/parameter profiles, semantic search over similar tasks, and a searchable tool catalog.
  - Work on the next task while a submission is pending.
  - Revisit tasks repeatedly; the first accepted improvement is rarely optimal.
  - A single agent produced roughly 30-40 accepted submissions and about 10 rejected attempts per eight-hour run, with median accepted gain around 0.21.
  - Compactly expressing the correct task rule remained more effective than generic neural training.
  - DAG-chain enumeration over ONNX operators was useful for micro-gains, but the author did not expect that lane alone to break 7000.
- `704762`, Tony Li / Yiheng Wang:
  - Record every failed optimization and feed that failure memory back into later attempts.
  - Profiling reduced a >30 minute workflow to about 12 minutes at the 74xx level without reducing score.
  - Synthetic validation is a risk signal, not an absolute gate: valid Kaggle solutions can fail synthetic examples.
  - Overfit-risk tasks: `192,319,118,359,018,285,096,048,355,219`.
  - Slow tasks: `358,350,212,335,246,022,375,009,074,070`.
- `704006`, Tony Li:
  - Bottom 15: `158,233,173,054,025,285,366,133,286,255,349,018,187,145,243`.
  - Another high-ranked team scored 232.16 on the same 15 tasks versus Tony's 227.716, proving substantial task-level headroom.
  - Manual/LLM golfing still found individual +2 point improvements in mid-tier tasks.
  - Last year's Python length is only a rough prompt anchor. BFS, copy/paste and shape recognition transfer poorly to this year's ONNX objective.

## Operator and Tooling Leads

- `703462`, GLM vs Opus: the strongest deploy-safe motifs were algebraic/narrow-dtype rewrites and collapsing repeated branches into one batched operation. Exact validation and full context were decisive.
- `699313` and `699429`: Chris Deotte's ONNX GUI and `goldbar123467/GolfWebGUI` support human-in-the-loop graph inspection. The repository previously had an unsafe default Hugging Face target, so upload ownership must be verified before use.
- `698637`: public EDA confirms that competitive ONNX files are symbolic tensor programs, not conventional trained neural networks.

## Project Decisions

1. Keep submissions asynchronous; poll the previous result before submitting the next candidate.
2. Prioritize semantic ARC-DSL compiler templates and per-task repeated passes over blind public-bundle mixing.
3. Treat synthetic/ARC-GEN failures as risk evidence unless the official examples also fail.
4. Do not pursue fixed scorer exploits documented in early host-update threads; those paths were patched and rescored.

No private or hidden-test information was used.
