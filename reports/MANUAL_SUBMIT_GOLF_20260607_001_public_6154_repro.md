# Notebook Output Submit: GOLF_20260607_001_public_6154_repro

Status: submitted automatically via Kaggle CLI kernel output.

```bash
kaggle competitions submit neurogolf-2026 -k muelsyse111/neurogolf-submit-current -v 3 -f submission.zip -m "GOLF_20260607_001_public_6154_repro | public 6154 baseline closure | source=SRC_KAGGLE_NOTEBOOK_OCTAVIO_6154 | changed=all | local=pass"
```

Submission id: `53450566`
Current status: `COMPLETE`
Public score: `6154.71`

The manual flow below is retained as fallback.

1. Open Kaggle Notebook `muelsyse111/neurogolf-submit-current`:

```text
https://www.kaggle.com/code/muelsyse111/neurogolf-submit-current
```

It has been pushed as version 3 and reads the private Kaggle dataset `muelsyse111/neurogolf-current-candidate`.

To repush if needed:

```bash
kaggle kernels push -p notebooks
```

2. Run the notebook and confirm `/kaggle/working/submission.zip` appears in output. This session already downloaded `notebooks/output/submission.zip`; its 400 ONNX members match the local candidate by SHA256.
3. Submit that notebook output file to competition `neurogolf-2026`.
4. Use this submit message:

```text
GOLF_20260607_001_public_6154_repro | public 6154 baseline closure | source=SRC_KAGGLE_NOTEBOOK_OCTAVIO_6154 | changed=all | local=pass
```

5. After the public score appears, run:

```bash
python scripts/10_record_lb_result.py --exp-id GOLF_20260607_001_public_6154_repro --submission-id <id> --public-score <score>
```
