# First-Place Contact and Slack Collaboration Plan

last_updated: 2026-07-18
scope: NeuroGolf 2026 public-source collaboration

## Status

The final leaderboard CSV was downloaded through the Kaggle CLI on 2026-07-18.
`Kaggle Agent` finished first with `8314.03`. The verified final top-10 and
ranked public-solution review are in
`reports/FINAL_LEADERBOARD_TOP_SOLUTIONS_RETROSPECTIVE.md`.

Public first-place/high-rank source routes currently worth following:

- `1st Place - Introduction`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726654
- `Pipeline overview`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726799
- `Self Evolving Prompts`: https://www.kaggle.com/competitions/neurogolf-2026/discussion/726883
- Chris Deotte ONNX GUI discussion: https://www.kaggle.com/competitions/neurogolf-2026/discussion/699313
- Clark Kitchen open-source GUI discussion: https://www.kaggle.com/competitions/neurogolf-2026/discussion/699429
- Google Code Golf 2025 CGI writeup: https://www.kaggle.com/competitions/google-code-golf-2025/writeups/cgi
- CGI public repository: https://github.com/Seek64/NeurIPS-Code-Golf-2025

## Public Contact Policy

Allowed contact paths:

- Reply on the public Kaggle writeup or discussion thread.
- Comment on the author's public Kaggle notebook when the question is notebook-specific.
- Open a GitHub issue or PR only when the author has linked a public repository and the question is about that repository.
- Use Hugging Face discussions/issues only for repositories explicitly published by the author.
- Use teammate Slack for internal coordination, never for sharing hidden data or private leaks.

Not allowed:

- Scraping private emails, private social accounts, or hidden profile details.
- Asking for non-public hidden test answers, private leaderboard data, or unreleased artifacts.
- Sharing Kaggle tokens, Hugging Face tokens, notebook credentials, or private dataset credentials in Slack or Git.

Safe account references:

- Kaggle notebook submissions in this workspace have used the public account/kernel namespace `muelsyse111`.
- GitHub remotes use `git@github.com:whzy3185/kagglegolf.git` and `git@github.com:whzy3185/kaggleneurogolf-2026.git`.
- Credential files must stay outside Git, normally under the user's Kaggle CLI configuration such as `%USERPROFILE%\.kaggle\kaggle.json`.

## Message Template for Public First-Place Threads

```text
Hi, we are studying the public NeuroGolf writeup and trying to reproduce the engineering workflow, not hidden answers. Could you clarify one public implementation detail?

Question:
- <specific question about task notes, prompt evolution, candidate selection, runtime budget, or validation>

Context:
- We are using official validator/scorer only.
- We keep task-level provenance and do not use private data.
- Any answer can stay public in this thread.

Thanks.
```

Use one question per comment. Do not ask for their final artifact unless it is already public.

## Slack Operating Model

Recommended channels:

- `#ngc-intel`: Kaggle Code, Discussion, writeups, public repos, source registry.
- `#ngc-submissions`: candidate IDs, package SHA, Kaggle submission ID, score, rollback decision.
- `#ngc-taskbank`: task-level deltas, accepted models, rejected pairs, high-memory tasks.
- `#ngc-onnx-surgery`: graph rewrite motifs, before/after cost, runtime failures.
- `#ngc-rules-risk`: scorer-boundary ideas, host clarifications, compliance holds.

Recommended roles:

- Source scout: refreshes public notebooks, discussions, writeups, GitHub/HF repos.
- Reproducer: downloads public outputs, validates structure, records source IDs.
- Task banker: updates per-task candidates, deltas, negative evidence, and next batches.
- ONNX surgeon: implements exact graph rewrites and cost reductions.
- Submission captain: owns queue, Kaggle kernel output, submit logs, score polling.
- Recorder: keeps retrospectives, Slack decisions, and GitHub docs current.

## Slack Handoff Format

```text
exp_id:
parent_exp_id:
changed_tasks:
source_id:
direction:
local_validation:
official_score_or_cost_delta:
artifact_sha:
submission_id:
public_score:
decision:
next_action:
owner:
```

Every Slack claim that affects a candidate must be copied into Git as a report, CSV row, manifest field, or task note before it changes the submission queue.

## Lessons from the First-Place Direction

The public first-place writeup direction emphasizes a knowledge system rather than a single magic ONNX trick:

- Each task needs notes, facts, failure paths, candidate builders, and public-source provenance.
- Agents should compete on bounded task objectives, then successful tactics are promoted into a shared cookbook.
- Structural rewrites and solver replacements are more valuable than indefinite small cleanups.
- Runtime and memory budget should be modeled as a 400-item portfolio problem, not as isolated per-task wins.
- Negative evidence must survive; repeated failures from the same source family should alter priority, not disappear.

## Immediate Team Actions

1. Post only focused public questions on the first-place discussions and GUI threads.
2. Mirror every public answer into `research/EVIDENCE_REGISTRY.md` or a dated report.
3. Keep Slack as coordination, not the source of truth.
4. Keep private credentials out of Slack and Git.
5. Use the first-place workflow to improve our task-bank and candidate-selection system, not to request private artifacts.
