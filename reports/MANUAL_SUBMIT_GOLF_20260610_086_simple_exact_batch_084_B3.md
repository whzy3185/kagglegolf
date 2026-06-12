# Manual Submit: GOLF_20260610_086_simple_exact_batch_084_B3

reason: primary and fallback kernel push failed; primary=400 Client Error: Bad Request for url: https://api.kaggle.com/v1/kernels.KernelsApiService/SaveKernel
; fallback=Expecting value: line 1 column 1 (char 0)
; local zip submit also failed: Traceback (most recent call last):
  File "E:\anaconda\Lib\site-packages\urllib3\connectionpool.py", line 787, in urlopen
    response = self._make_request(
        conn,
    ...<10 lines>...
        **response_kw,
    )
  File "E:\anaconda\Lib\site-packages\urllib3\connectionpool.py", line 534, in 

Candidate: `E:\kagglegolf\submissions\candidates\GOLF_20260610_086_simple_exact_batch_084_B3`
Kernel: ``
Expected output: `submission.zip`

1. Open Kaggle Code kernel ``.
2. Confirm the latest successful output contains `submission.zip`.
3. Submit `submission.zip` to competition `neurogolf-2026`.
4. Use this submit message:

```text
GOLF_20260610_086_simple_exact_batch_084_B3 | target7800 aggressive candidate | source=SRC_ARC_DSL_GITHUB | changed=task300,task309,task380 | risk=medium | local=pass
```

5. Poll and record:

```bash
python scripts/20_poll_submission_results.py --exp-id GOLF_20260610_086_simple_exact_batch_084_B3
python scripts/09_query_submission_history.py
```
