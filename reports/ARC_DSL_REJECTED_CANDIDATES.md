# ARC-DSL Rejected Candidates

## task036 largest connected component crop

- source: SRC_ARC_DSL_GITHUB
- rule: `objects(diagonal=True) -> argmax(size) -> subgrid`
- local correctness: 265/265
- implementation: per-color local-density selection followed by dynamic bbox crop
- current official memory: 79832
- candidate official memory: 115252
- current official points: 13.710918
- candidate official points: 13.343702
- decision: reject; correct but structurally more expensive than the current graph

The compiler remains available as a reusable topology experiment, but task036
must not enter the submission queue without a lower-memory selection method.
