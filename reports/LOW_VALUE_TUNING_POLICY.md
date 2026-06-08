# Low-Value Tuning Policy

The current strategy mode is aggressive structural exploration. Candidates that
only make cosmetic or tiny local edits are not valid leaderboard pushes unless
they are bugfixes or descendants of an experiment with confirmed positive
feedback.

## Default Reject

The following candidates are rejected by default:

1. Only metadata, node names, or tensor names changed.
2. Only `doc_string` or other descriptive fields removed.
3. Only a small number of constants changed.
4. Only dtype or layout changed while the main graph topology is unchanged.
5. Only small `Identity`, `Cast`, `Reshape`, or `Transpose` cleanup.
6. Missing `source_id`, `direction_id`, or any Evidence Gate basis.
7. Broad mix without positive single-task or top-k probe feedback.
8. Duplicate package hash.
9. Local validation failure.

## Allowed

The following are valid aggressive exploration directions:

1. Full bundle replacement.
2. Solver replacement.
3. Operator family replacement.
4. Large subgraph rewrite.
5. Memory-footprint structural surgery.
6. High-risk scorer-boundary candidate, isolated in the high-risk lane.
7. Bottom15 single-task or top-k targeted probe.
8. P0/P1 public high-score source task-harvest candidate.

