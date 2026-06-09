# Research Source Refresh - 2026-06-09

## Current Competition

- Confirmed effective submission quota: 100/day via Kaggle staff topic `703112`.
- Confirmed current objective: cumulative memory footprint plus parameter count; MACs removed via host topic `696953`.
- Confirmed pinned stack via topic `693088`.
- Added high-rank workflow evidence from topics `703914`, `704762` and `704006`.

## Historical Competition

- Downloaded the 2025 Google Code Golf final public leaderboard.
- Imported the first-place Code Golf International write-up.
- Recorded the winning repository and final commit:
  `Seek64/NeurIPS-Code-Golf-2025@9a5d156eabdc35732688751c091bf57277f70c21`.
- Local repository clone was attempted over HTTPS and SSH but failed due network reset/timeout. The public write-up and Kaggle metadata remain sufficient for strategy extraction.

## Strategy Changes

1. Build reusable static ONNX compilers for ARC-DSL semantic families.
2. Prioritize high-current-cost tasks with exact official and ARC-GEN validation.
3. Maintain task dossiers and failed-rewrite memory.
4. Continue candidate work while Kaggle submissions are pending.
5. Use public bundles as task sources and score references, not indiscriminate broad-mix replacements.

## Next Compiler Families

- `objects -> argmax -> subgrid`
- `leastcolor -> ofcolor -> subgrid`
- `numcolors -> decrement -> upscale`
- fixed mirror/rotation and concatenate transforms
- small neighborhood and candidate-enumeration templates
