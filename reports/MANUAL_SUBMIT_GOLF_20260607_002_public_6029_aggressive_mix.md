# Manual Submit: GOLF_20260607_002_public_6029_aggressive_mix

reason: kernel output did not contain submission.zip: HTTPSConnectionPool(host='api.kaggle.com', port=443): Max retries exceeded with url: /v1/kernels.KernelsApiService/ListKernelSessionOutput (Caused by ProxyError('Unable to connect to proxy', RemoteDisconnected('Remote end closed connection without response')))


Candidate: `E:\Jitter\kagglegolf\submissions\candidates\GOLF_20260607_002_public_6029_aggressive_mix`
Kernel: `muelsyse111/neurogolf-submit-current`
Expected output: `submission.zip`

1. Open Kaggle Code kernel `muelsyse111/neurogolf-submit-current`.
2. Confirm the latest successful output contains `submission.zip`.
3. Submit `submission.zip` to competition `neurogolf-2026`.
4. Use this submit message:

```text
GOLF_20260607_002_public_6029_aggressive_mix | target7000 aggressive candidate | source=SRC_KAGGLE_NOTEBOOK_JSRDCHT_6029 | changed=task286,task173,task054 | risk=high | local=pass
```

5. Poll and record:

```bash
python scripts/20_poll_submission_results.py --exp-id GOLF_20260607_002_public_6029_aggressive_mix
python scripts/09_query_submission_history.py
```
