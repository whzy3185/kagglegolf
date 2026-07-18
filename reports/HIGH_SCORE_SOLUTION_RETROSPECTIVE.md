# NeuroGolf Repository Score Path and Public-Bundle Retrospective

last_updated: 2026-07-18
source_scope: public Kaggle bundles reproduced by this repository and local score records

## Scope

This file documents this repository's `7015 -> 7113 -> 7266 -> 7395 -> 7420`
path. Those numbers are not the final leaderboard leaders' scores.

For the final top-10 leaderboard and the actual first-place through tenth-place
public solution review, see
`reports/FINAL_LEADERBOARD_TOP_SOLUTIONS_RETROSPECTIVE.md`.

## Current Local State

- Current best recorded in this repository: `7420.93`
- Best submission id: `54736568`
- Best exp_id/message: `submission5 all400 GitHub audit safe11 +1.025027 sha bcef5a06`
- Target recorded in the current scorecard: `7800.0`
- Final leaderboard snapshot downloaded on 2026-07-18: winner `Kaggle Agent`,
  score `8314.03`.

## Public High-Score Sources Already Reproduced or Audited

| Source | Public path | Verified local/account result | Main value |
| --- | --- | ---: | --- |
| SajayR 7015 | https://www.kaggle.com/code/sajayr/neurogolf-7015 | `7015.36` | First direct public 7k reproduction; useful as a full-bundle and task-bank source. |
| Franksunp 7113 | https://www.kaggle.com/code/franksunp/starter-baseline-compact-onnx-artifact-vi | `7113.63` | Public blend recorded as 376 SajayR picks and 24 Kojimar picks; proved task-level artifact selection beats one-source replacement. |
| Prvsiyan 7266.72 | https://www.kaggle.com/code/prvsiyan/neurogolf-7266-72-w-visualizations | `7266.72` | Strong public visualization/repro baseline; confirmed local task-table total was close to public score. |
| Kaggloop 7266.48 | https://www.kaggle.com/code/ryosukeshiroshita/neurogolf-7266-48-github-com-qurore-kaggloop | public code source | Shows reproducible loop design: scorer replay, min-merge, terminal operators, low-rank Einsum, GridSample, ConvInteger, and crop-like rewrites. |
| Beicicc 6645 | https://www.kaggle.com/code/beicicc/neurogolf-6645-39-public-score-open-solution | lower than later public sources | Useful as a structural motif source; raw broad structural-pass mixing caused negative feedback in this workspace. |
| Kojimar 6272 | https://www.kaggle.com/code/kojimar/6272-50-lb-audited-neurogolf-onnx-overrides | public source family | Useful for audited overrides and task-level attribution patterns. |

## Cross-Reference to Final-Leaderboard Writeups

The detailed rank-by-rank review is maintained in
`reports/FINAL_LEADERBOARD_TOP_SOLUTIONS_RETROSPECTIVE.md`. The source links
below are retained here only because they influenced this repository's later
workflow:

- `1st Place - Introduction`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726654
- `Pipeline overview`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726799
- `Self Evolving Prompts`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726883
- `6th Place Solution - Claudex`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726691
- `9th Place Gold - Pavel & CroDoc`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726782
- `10th Place Solution`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726653

Reusable lessons:

- Keep a task memory plus a longer archive; do not load every historical detail into every worker.
- Make each task a durable unit: current ONNX, builder, task notes, candidates, validation, cost history, online deltas.
- Run mini-contests across agents for the same bounded objective, then distill the winner into a cookbook.
- Move between vertical task work and horizontal transfer to similar tasks.
- Track runtime and memory budget globally; the final 400-model package is a portfolio selection problem.
- Submit small or medium batches for attribution, then merge only online-confirmed families into the parent.

## Google Code Golf 2025 Transfer

Sources:

- Kaggle competition: https://www.kaggle.com/competitions/google-code-golf-2025
- CGI first-place writeup: https://www.kaggle.com/competitions/google-code-golf-2025/writeups/cgi
- CGI repository: https://github.com/Seek64/NeurIPS-Code-Golf-2025

Transferable strategy:

- Revisit tasks repeatedly; one pass across 400 tasks is not enough.
- Maintain task-specific Python or DSL solvers as semantic references even when final output must be ONNX.
- Use enumerate-and-verify search for recurring ARC motifs.
- Convert solver families into compact graph templates only after correctness is pinned down.
- Preserve failed attempts; later solver families often reuse old negative evidence.

## Our Score Path After Public Source Harvest

This repository's later score movement came from combining public-source adoption with parent-bound exact changes:

1. `7015.36`: direct SajayR public notebook output.
2. `7113.63`: Franksunp public blend output.
3. `7266.72`: Prvsiyan public visualization/repro output.
4. `7270+ to 7297+`: parent-bound C-task exact and local stack experiments.
5. `7378+`: all-399 public-source campaign and team package integration.
6. `7395.79`: exact self-Einsum tasks `017` and `197`.
7. `7410+`: terminal factorization, CP factorization, selector rewrites, and exact cleanup batches.
8. `7420.93`: final team package integration recorded by submission `54736568`.

## What Worked

- Directly reproducing stronger public bundles before attempting local invention.
- Diffing public bundles by task and rebasing only strict winners onto the current parent.
- Keeping deterministic package SHA and model SHA records.
- Using exact graph transforms with clear shape assumptions.
- Isolating high-risk or shape-sensitive tasks before stacking.
- Treating negative online feedback as a durable task-bank fact.

## What Failed or Was Risky

- Broad structural-pass mixing without positive probe feedback.
- Calling a transform exact after testing only public shapes.
- Relying on local correctness while ignoring target runtime compatibility.
- Allowing stale parent artifacts into later candidates.
- Letting raw public artifacts weaken provenance and task-level attribution.

## Next Collaboration Priorities

1. Ask public first-place/top-writeup authors only about workflow details that can be answered publicly.
2. Convert every high-score source into a task-level candidate table, not just a submission.zip archive.
3. Keep Slack aligned around task ownership, validation proof, cost deltas, and package lineage.
4. Use CGI/ARC-DSL solutions as semantic references for ONNX builders, not as direct code-golf byte tricks.
5. Continue parent-bound exact transforms and source-safe task-level overlays rather than repeating broad low-attribution bundles.
