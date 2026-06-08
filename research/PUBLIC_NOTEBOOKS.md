# Public Notebooks

Captured on 2026-06-07 via Kaggle CLI. Refreshed on 2026-06-08.

P0:
- `octaviograu/6154-71-onnx-rewrites-hand-built-solvers`, claimed 6154.71, dataset `octaviograu/neurogolf-manual-rewrites-v205`, reproduced as first candidate.
- `jsrdcht/6029-09-lb-neurogolf-all-task-onnx-solution`, claimed 6029.09, dataset `jsrdcht/neurogolf-6029-submission-bundle`, downloaded as fallback and diff source.
- `beicicc/neurogolf-6645-39-public-score-open-solution`, claimed 6645.39, public output downloaded on 2026-06-07; broad structural-pass mix submitted as `GOLF_20260608_004b_beicicc_structural_pass_mix` scored 5948.07, so retain only for targeted task probes.
- `mirzayasirabdullah07/best-score-neurogolf-championship-notebook`, discovered 2026-06-08; partial output downloaded with 308 task files, build structural-pass harvest next.
- `biohack44/neurogolf-super-blend-best-public-score`, discovered 2026-06-08; partial output downloaded with 288 task files, build structural-pass harvest next.
- `afr1ste/neurogolf-5689-51-current-rules-open-solution`, claimed 5689.51, imported as lower baseline artifact source.

P1:
- `vyankteshdwivedi/neurogolf-multi-source-onnx-solver`, public output downloaded on 2026-06-07; likely useful for cross-source task harvesting.
- `jonathanchan/ngc26-constraint-smart-logic-mix-blending`, high-vote constraint/logic blend; zip downloaded, full replace failed on 3 tasks, structural-pass mix `GOLF_20260608_008b_jonathan_structural_pass_mix` scored 5595.78, so use only for targeted task probes.
- `seddiktrk/surgical-onnx-precision-parameter-reduction`, memory/parameter surgery source for rewrite lane.
- `jsrdcht/glm-vs-opus-onnx-cost-opt-neurogolf-2026`, next import for cost-opt motifs.
- `biohack44/neurogolf-2026-fp16-surgery-prune-blend-6115`
- `nadeembinshajahan/neurogolf-2026-fp16-surgery-prune-blend-6130`
- `nadeembinshajahan/6151-lb-neurogolf-2026-stable-fp16-surgery`
- `kojimar/5800-55-lb-neurogolf-task-level-onnx-blend` appears as a kernel source in the 6029 metadata.

Rejected candidate note:
- `GOLF_20260607_004_public_notebook_full_replace` from the imported 6645 artifact failed structural validation because many models include `bad_opset_domain:golf` and `has_functions`; do not submit until normalized.

Next action: submit validator-pass 6029 probes, then import Mirza/Biohack/Jonathan public outputs for 7000+ pursuit.
