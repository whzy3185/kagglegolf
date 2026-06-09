# Historical Writeups

## 2025 Google Code Golf Championship

Source: [1st place write-up: Code Golf International](https://www.kaggle.com/competitions/google-code-golf-2025/writeups/cgi)

Final leaderboard snapshot downloaded on 2026-06-09:

| rank | team | score | submissions |
|---:|---|---:|---:|
| 1 | Code Golf International | 962070 | 384 |
| 2 | jailctf merger | 961805 | 169 |
| 3 | ox jam! | 961784 | 330 |
| 4 | FuunAgent | 957810 | 573 |
| 5 | HIMAGINE THE FUTURE. | 957568 | 51 |

Champion repository: `https://github.com/Seek64/NeurIPS-Code-Golf-2025`

Final submission commit: `9a5d156eabdc35732688751c091bf57277f70c21`

Reproduction command documented by the winners: `python auto_zip.py`.

### Transferable Strategy

- Five experienced golfers manually optimized all 400 tasks and repeatedly revisited solutions.
- Recurring semantic motifs were turned into compact building blocks: transpose, mirrors, rotations, flatten/filter, color-frequency selection, repeated transforms, neighborhood scans and guess-and-check.
- Candidate enumeration was especially effective when verification was simpler than direct search.
- `pysearch` was used to synthesize short formulas and iterated transforms.
- Public per-task score benchmarks were described as invaluable.
- The winner used compression on only 21/400 tasks. The dominant advantage came from task-specific semantic work and repeated review, not one global compressor.

### NeuroGolf Translation

- Convert recurring Python motifs into reusable static-shape ONNX compiler templates.
- Build a per-task dossier containing the ARC rule, current graph cost, previous failed rewrites and public score feedback.
- For search-friendly tasks, enumerate small legal ONNX DAGs and verify exact outputs.
- Revisit each promising task several times instead of treating the first improvement as final.
- Use the 2025 task score/solution length only as a rough complexity prior. Python byte tricks, regex and zlib do not directly optimize the current memory-plus-parameters objective.

## Other Historical Sources

- ARC Prize 2024 technical report: program synthesis, validation loops and test-time reasoning.
- ARC-GEN / RE-ARC / ARC-DSL: generator adapters, DSL primitives and public task-level solver references.
- No prior same-name NeuroGolf competition was found; Google Code Golf 2025 is the direct historical ARC code-golf analogue.

Historical materials are strategy evidence, not hidden-answer sources.
