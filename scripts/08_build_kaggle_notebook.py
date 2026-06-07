from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
from datetime import datetime

from _bootstrap import ROOT
from neurogolf.notebook_builder import build_kernel_metadata, build_submission_notebook
from neurogolf.paths import root
from neurogolf.provenance import git_commit
from neurogolf.reports import append_block


def latest_candidate() -> str:
    candidates = sorted([p for p in root("submissions/candidates").iterdir() if p.is_dir()])
    if not candidates:
        raise SystemExit("No candidate directory found. Run script 06 first.")
    return candidates[-1].name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-id", default="")
    parser.add_argument("--dataset-slug", default="")
    args = parser.parse_args()
    exp_id = args.exp_id or latest_candidate()
    candidate = root("submissions/candidates", exp_id)
    manifest = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
    dataset_slug = args.dataset_slug or manifest.get("dataset_slug") or "octaviograu/neurogolf-manual-rewrites-v205"
    source_id = manifest.get("source_id", "")
    notebook_path = root("notebooks/kaggle_submit_current.ipynb")
    embed_path = None if args.dataset_slug else candidate / "submission.zip"
    build_submission_notebook(
        notebook_path,
        exp_id=exp_id,
        source_ids=[source_id],
        dataset_slug=dataset_slug,
        source_subdir="submission" if "octaviograu" in dataset_slug else "",
        git_commit=git_commit(),
        embedded_zip_path=embed_path,
    )
    build_kernel_metadata(root("notebooks/kernel-metadata.json"), notebook_path.name, [dataset_slug])
    payload_path = root("notebooks/submission_payload.b64")
    zip_path = candidate / "submission.zip"
    if zip_path.exists() and embed_path is not None:
        payload_path.write_text(base64.b64encode(zip_path.read_bytes()).decode("ascii"), encoding="utf-8")
    shutil.copy2(notebook_path, candidate / "notebook.ipynb")

    manual = root("reports", f"MANUAL_SUBMIT_{exp_id}.md")
    manual.write_text(
        f"""# Manual Notebook Output Submit: {exp_id}

1. Open Kaggle Notebook `muelsyse111/neurogolf-submit-current`, or push it with:

```bash
kaggle kernels push -p notebooks
```

2. Run the notebook and confirm `/kaggle/working/submission.zip` appears in output.
3. Submit that notebook output file to competition `neurogolf-2026`.
4. Use this submit message:

```text
{exp_id} | public 6154 baseline closure | source={source_id} | changed=all | local=pass
```

5. After the public score appears, run:

```bash
python scripts/10_record_lb_result.py --exp-id {exp_id} --submission-id <id> --public-score <score>
```
""",
        encoding="utf-8",
    )
    append_block(
        root("reports/SUBMISSION_ATTEMPTS.md"),
        f"""## {exp_id} notebook update

created_at: {datetime.now().isoformat(timespec="seconds")}
notebook_path: notebooks/kaggle_submit_current.ipynb
candidate_notebook_path: submissions/candidates/{exp_id}/notebook.ipynb
manual_submit_doc: reports/MANUAL_SUBMIT_{exp_id}.md
status: ready_for_kaggle_notebook_output
""",
    )
    print(notebook_path)
    print(manual)


if __name__ == "__main__":
    main()
