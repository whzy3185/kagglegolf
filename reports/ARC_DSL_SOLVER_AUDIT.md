# ARC-DSL Solver Audit

checked_at: 2026-06-09T12:55:17
mapped_tasks: 400/400
official_train_test_pass: 399/400
official_plus_arc_gen_pass: 280/400
candidate_dir: submissions/candidates/GOLF_20260608_046_rogermt_positive_stack_255_128_208/onnx

## Architecture Decision

NeuroGolf task numbering maps exactly to the public ARC-AGI training set.
Use ARC-DSL programs as task-level solver specifications and compile the
highest-loss, shortest programs into compact ONNX graphs.

## Top Compile Priorities

| task | ARC id | DSL calls | current utility | priority | all examples |
|---|---|---:|---:|---:|---|
| task249 | a416b8f3 | 1 | 15.813133 | 9.1869 | true |
| task223 | 9172f3a0 | 1 | 15.895020 | 9.1050 | true |
| task307 | c59eb873 | 1 | 15.895020 | 9.1050 | true |
| task150 | 67a3c6ac | 1 | 17.831420 | 7.1686 | true |
| task155 | 68b16354 | 1 | 17.831420 | 7.1686 | true |
| task380 | ed36ccf7 | 1 | 18.325439 | 6.6746 | true |
| task087 | 3c9b0459 | 1 | 18.931574 | 6.0684 | true |
| task140 | 6150a2bd | 1 | 18.931574 | 6.0684 | true |
| task326 | d10ecb37 | 1 | 19.924826 | 5.0752 | true |
| task130 | 5614dbcf | 2 | 15.295085 | 4.8525 | false |
| task276 | b1948b0a | 1 | 20.500190 | 4.4998 | true |
| task309 | c8f0f002 | 1 | 20.500190 | 4.4998 | true |
| task337 | d511f180 | 1 | 20.500190 | 4.4998 | true |
| task303 | c1d99e64 | 3 | 13.686135 | 3.7713 | true |
| task036 | 1f85a75f | 3 | 13.701407 | 3.7662 | true |
| task300 | be94b721 | 3 | 13.731825 | 3.7561 | true |
| task070 | 32597951 | 3 | 13.897783 | 3.7007 | true |
| task014 | 0b148d64 | 3 | 14.359971 | 3.5467 | false |
| task129 | 5582e5ca | 2 | 18.059778 | 3.4701 | true |
| task049 | 23b5c85d | 3 | 14.649234 | 3.4503 | false |
| task310 | c909285e | 3 | 14.814044 | 3.3953 | true |
| task289 | b91ae062 | 3 | 14.860966 | 3.3797 | true |
| task242 | 9ecd008a | 3 | 15.073187 | 3.3089 | true |
| task031 | 1cf80156 | 3 | 15.146333 | 3.2846 | true |
| task188 | 7b7f7511 | 3 | 15.665320 | 3.1116 | false |
| task067 | 2dee498d | 2 | 18.897441 | 3.0513 | true |
| task269 | ac0a08a4 | 3 | 15.903276 | 3.0322 | true |
| task135 | 5bd6f4ac | 2 | 19.113896 | 2.9431 | true |
| task029 | 1c786137 | 4 | 13.508043 | 2.8730 | false |
| task384 | f25fbde4 | 4 | 13.767185 | 2.8082 | true |
