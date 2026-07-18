# NeuroGolf 2026 Final Leaderboard and Top-Solution Retrospective

last_updated: 2026-07-18
scope: final leaderboard leaders and their public post-competition solution material
source_of_rank_truth: Kaggle final leaderboard CSV downloaded on 2026-07-18

## Scope Correction

The `7015 -> 7113 -> 7266 -> 7395 -> 7420` sequence is this repository's
public-bundle adoption and team score path. It is not the final leaderboard
leaders' score path.

The final winner scored `8314.03`. This document is the leaderboard-top
retrospective. The repository's own path remains documented separately in
`reports/HIGH_SCORE_SOLUTION_RETROSPECTIVE.md`.

## Final Top 10

| rank | team | final score | submissions | members |
| ---: | --- | ---: | ---: | --- |
| 1 | Kaggle Agent | 8314.03 | 6798 | arc144, cdeotte, jiweiliu, maxjeblick, titericz |
| 2 | neurogolf team | 8243.89 | 7621 | chankhavu, gufanmingmie, jacekwl, yeoyunsianggeremie, yhirano |
| 3 | The Final Ensemble | 8221.27 | 5586 | christofhenkel, dziyanavalenta, fritzcremer, tomirol, tonylica |
| 4 | WeLuvEleven | 8168.59 | 5909 | datathinker1, evolvion, fengstar, kirvk013, sunning11 |
| 5 | M & H & M & N & M | 8142.02 | 3479 | honganzhu, maciejsypetkowski, maxchen303, mrmldjr, nataliajakowska |
| 6 | claudex | 8118.97 | 2622 | binhdth, buphmquc, hainguyenthien, myotterspace, pntan17 |
| 7 | Slow and Steady | 8067.63 | 5992 | chaitanyagarg2, masasato1999, paritoshtripathi5, tivfrvqhs5, yash9439 |
| 8 | kluges clueless | 8048.16 | 5468 | alexeyshmelev, fastlight2007, ivangevorkov, nikitachervov, noobanot |
| 9 | Pavel & CroDoc | 8038.62 | 6555 | crodoc, pavelsavchenkov |
| 10 | Timeout exceeded : ( | 8028.25 | 1631 | yiheng |

Leaderboard command:

```bash
kaggle competitions leaderboard neurogolf-2026 --download
```

The downloaded CSV was named
`neurogolf-2026-publicleaderboard-2026-07-18T14:00:07.csv`.

## 1st Place: Kaggle Agent, 8314.03

Team:

- Chris Deotte (`cdeotte`)
- Giba (`titericz`)
- Jiwei Liu (`jiweiliu`)
- Max Jeblick (`maxjeblick`)
- Eduardo Rocha de Andrade (`arc144`)

Public sources:

- [Introduction](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726654)
- [Pipeline overview](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726799)
- [Self Evolving Prompts](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726883)
- [Team dashboard](https://daxiongshu.github.io/kaggle-agent-neurogolf-2026/)

Verified lessons:

- Architectural rewrites averaged about `+0.5` per task, while polishing an
  existing graph averaged about `+0.05`. Their system explicitly pushed agents
  toward a new representation instead of endless pruning.
- The pipeline alternated vertical single-task exploration with horizontal
  multi-task transfer. A new trick was mined from a deep task session, added to
  a cookbook, and then searched across related tasks.
- A worker received a concrete target, task facts, rule notes, current graph and
  cost profile, previous dead ends, reusable utilities, human ARC references,
  and the shared cookbook.
- Validation used official examples, ARC-GEN, and additional randomized or
  color-varied inputs where appropriate.
- Their shared dashboard retained several candidates per task with score and
  runtime. Final package selection used a Multiple-Choice Knapsack formulation
  to trade score against the global runtime limit.
- They kept both a best package at roughly 30 minutes and a faster package
  around 18 minutes that still scored about 8310.
- ChatGPT Pro was used for long single-turn architectural search. Chris reported
  an average thinking time near 80 minutes and, once the team was above 7900,
  success rates around 33% for a `+0.5` target and 50% for a `+0.3` target.
- Self-evolving prompts were selected through mini-contests. Successful agent
  context was promoted into manager guidance and reusable cookbooks.

Direct implication for our workflow:

1. Track multiple valid `(score, runtime, architecture)` candidates per task.
2. Make architecture replacement the default plateau response.
3. Add explicit target gains and theoretical lower-bound reasoning to task prompts.
4. Run horizontal transfer whenever a new terminal-operator or basis trick wins.
5. Select the final 400-task package under runtime as a portfolio problem.

## 2nd Place: neurogolf team, 8243.89

No dedicated second-place solution post was found in the final discussion pages
checked on 2026-07-18. The final leaderboard and first-place discussion comments
confirm the team and placement, but there is not enough public method detail to
write a reliable technical reconstruction.

Action: watch for a later writeup from `chankhavu`, `gufanmingmie`, `jacekwl`,
`yeoyunsianggeremie`, or `yhirano`. Do not infer their pipeline from rank alone.

## 3rd Place: The Final Ensemble, 8221.27

No standalone third-place solution writeup was found in the checked final
discussion pages. Public comments in the first-place pipeline thread establish:

- Tony Li's team also used Multiple-Choice Knapsack package selection.
- Tony sometimes let Codex choose candidate models automatically.
- Their score discovery outpaced runtime optimization near the deadline, leaving
  promising improvements unsubmitted.
- A teammate, Matheus, found an architecture-rewrite breakthrough similar to the
  winner's plateau-breaking approach.

Source:

- [Three Things at the End of an Unforgettable Competition](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726651)
- Comments under the [first-place pipeline overview](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726799)

The evidence supports runtime-aware candidate selection and architecture search,
but not a more detailed reconstruction.

## 4th Place: WeLuvEleven, 8168.59

Source:

- [4th Place Solution Atlas](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726879)
- [Interactive research atlas](https://evolvion.com/competitions/neurogolf_400)

Verified lessons:

- Treat all 400 tasks as a portfolio of independent optimization campaigns.
- Preserve campaign history, model snapshots, task explorer data, technique
  catalogs, validation results, promotion decisions, and leaderboard feedback.
- Use the dashboard as an operational research system, not merely a score chart.

The post promised a more detailed writeup; this entry should be refreshed when
that material appears.

## 5th Place: M & H & M & N & M, 8142.02

Source:

- [5th Place Solution Writeup](https://www.kaggle.com/competitions/neurogolf-2026/discussion/727134)

Verified lessons:

- Store multiple models per task by hash with score, evaluation time, and online
  status (`unknown`, `correct`, or `broken`).
- Establish hidden correctness through grouped submissions and adaptive
  bisection. A broken model produced zero online, so bisection isolated it.
- Approximately maximize total score under summed runtime for final submission.
- Maintain an evolving idiom system. Agents vote on, annotate, and disable
  reusable tricks based on measured cross-task evidence.
- Change prompts based on bottleneck: architecture rethink after plateau, repair
  after validation failure, or runtime optimization for slow candidates.
- Add static operator checks beyond `onnx.checker`, including Conv bias length
  matching output channels.

This is the strongest public evidence for a task registry that stores several
candidate states rather than a single `best.onnx`.

## 6th Place: claudex, 8118.97

Sources:

- [6th Place Solution - Claudex](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726691)
- [Public repository](https://github.com/PNTAN17/neurogolf)

Verified lessons:

- Split tasks across two teams, then swap ranges every one or two days to escape
  human and agent local optima.
- Run Codex and ChatGPT streams in parallel.
- Use score-band operator libraries to suggest likely graph families.
- Prefer representation search: terminal `Einsum`, coordinate algebra,
  `ConvTranspose`, compact quantized classifiers, pooling/rank templates, and
  final-output fusion.
- Promote only strict scorer improvements or equal-score runtime gains.
- Gate candidates with checker, shape inference, ORT 1.24.4, all public examples,
  operator-specific checks, and 1000 fresh ARC-GEN samples.
- Probe risky tasks alone before merging them into a batch.

## 7th and 8th Place: Public Detail Still Incomplete

- [7th Place Solution - Slow and Steady](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726660)
- [8th Place writeup draft](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726693)

As checked on 2026-07-18, these posts contain draft visuals or a promise of a
later full writeup, but not enough text for a defensible technical retrospective.
Track them for updates; do not fill the gap with speculation.

## 9th Place: Pavel & CroDoc, 8038.62

Source:

- [9th Place Gold - Pavel & CroDoc](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726782)

Verified lessons:

- Both teammates often optimized the same tasks independently. They periodically
  merged per task, choosing higher verified score, then faster runtime on ties.
- A compact shared `MEMORY.md` held high-value patterns; a larger archive kept
  narrow discoveries. The compact memory was periodically deduplicated.
- The strongest gains came from representation changes, writing directly to
  output, recomputing instead of storing, and replacing canvas-sized state with
  small factors.
- Their main set had 202 one-node models and 273 models ending in `Einsum`.
- A task database accepted ONNX plus its builder only after full validation.
- Autonomous Codex sessions used persistent per-task idea logs; ChatGPT Pro was
  later used for deeper manual task sessions.
- Their local best was 8041.20 but exceeded the Kaggle runtime limit; the
  submitted package scored 8038.62.

## 10th Place: Yiheng Wang, 8028.25

Source:

- [10th Place Solution](https://www.kaggle.com/competitions/neurogolf-2026/discussion/726653)

Verified lessons:

- Every task was a three-file transactional unit: ONNX, reproducible builder, and
  durable task notes.
- A bounded scheduler kept a persistent multi-turn Codex session per task and
  performed backup, experiment, validation, then promote-or-restore.
- The scheduler used online changed-task probes and regression isolation to turn
  leaderboard feedback into the next search wave.
- A five-day unattended run improved the verified score by `+59.77`, changed 271
  models, retained 256 strict reductions and 15 cost-neutral rewrites, and kept
  zero regressions.
- ChatGPT handled semantic comparison and blank-slate architectures; Codex
  implemented and searched them at scale.
- Major graph ideas included direct-to-output terminal operators, recomputation
  instead of state, shared bases, finite-state or number-theoretic algebra,
  dynamic native operators, and preserving `Einsum` contraction order as model
  state.
- Python Code Golf solutions were used as semantic references, not mechanically
  copied into ONNX.

## Cross-Rank Consensus

The top public writeups converge on the same operating model:

1. One durable state space per task: model, builder, notes, attempts, cost, runtime.
2. Multiple candidate models per task, not one irreversible incumbent.
3. Strict validation and transactional promotion.
4. Architectural rewrites before endless local pruning.
5. Shared cookbooks or idiom registries built from measured cross-task wins.
6. Vertical deep exploration plus horizontal trick transfer.
7. Online probes and bisection for hidden failures.
8. Runtime-aware global package selection.
9. Persistent agent sessions or durable task memory to prevent rediscovery.
10. Human attention focused on targets, representations, validation policy, and
    knowledge distillation rather than editing every graph manually.

## Google Code Golf 2025 Transfer

Sources:

- [CGI first-place writeup](https://www.kaggle.com/competitions/google-code-golf-2025/writeups/cgi)
- [CGI repository](https://github.com/Seek64/NeurIPS-Code-Golf-2025)
- [Fourth-place parallel sampling writeup](https://www.kaggle.com/competitions/google-code-golf-2025/writeups/parallel-sampling-rule-based-prompt-generation)

Reusable strategy:

- Revisit all 400 tasks repeatedly rather than performing one static pass.
- Keep semantic Python solutions as a second representation of each ARC rule.
- Run parallel attempts, verify mechanically, retain the best valid candidate,
  and feed successful patterns into later prompts.
- Separate semantic discovery from target-format compression.
- Preserve failed methods as search memory.

The 2025 competition supplied the semantic and scheduling pattern. NeuroGolf's
leaders adapted it to ONNX graph representation, memory cost, runtime, and
agent-scale task portfolios.
