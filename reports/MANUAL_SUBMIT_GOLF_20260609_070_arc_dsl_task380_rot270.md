# Manual Submit: GOLF_20260609_070_arc_dsl_task380_rot270

reason: kernel-output submit failed: Traceback (most recent call last):
  File "E:\anaconda\Lib\site-packages\urllib3\connectionpool.py", line 787, in urlopen
    response = self._make_request(
        conn,
    ...<10 lines>...
        **response_kw,
    )
  File "E:\anaconda\Lib\site-packages\urllib3\connectionpool.py", line 534, in 

Candidate: `E:\kagglegolf\submissions\candidates\GOLF_20260609_070_arc_dsl_task380_rot270`
Kernel: `muelsyse111/neurogolf-submit-current`
Expected output: `submission.zip`

1. Open Kaggle Code kernel `muelsyse111/neurogolf-submit-current`.
2. Confirm the latest successful output contains `submission.zip`.
3. Submit `submission.zip` to competition `neurogolf-2026`.
4. Use this submit message:

```text
GOLF_20260609_070_arc_dsl_task380_rot270 | target7800 aggressive candidate | source=SRC_ARC_DSL_GITHUB | changed=task380 | risk=medium | local=pass
```

5. Poll and record:

```bash
python scripts/20_poll_submission_results.py --exp-id GOLF_20260609_070_arc_dsl_task380_rot270
python scripts/09_query_submission_history.py
```
