from __future__ import annotations

import json
import base64
from pathlib import Path


def dataset_input_dir(dataset_slug: str) -> str:
    return "/kaggle/input/" + dataset_slug.split("/")[-1]


def build_submission_notebook(
    path: Path,
    exp_id: str,
    source_ids: list[str],
    dataset_slug: str,
    source_subdir: str = "submission",
    git_commit: str = "unknown",
    embedded_zip_path: Path | None = None,
) -> None:
    input_dir = dataset_input_dir(dataset_slug)
    source_ids_repr = repr(source_ids)
    embedded_zip_b64_parts: list[str] = []
    payload_file_name = ""
    if embedded_zip_path and embedded_zip_path.exists():
        b64 = base64.b64encode(embedded_zip_path.read_bytes()).decode("ascii")
        embedded_zip_b64_parts = [b64[i : i + 1000] for i in range(0, len(b64), 1000)]
        payload_file_name = "submission_payload.b64"
    code = f"""
from pathlib import Path
import base64
import hashlib
import json
import shutil
import zipfile

EXP_ID = {exp_id!r}
GIT_COMMIT = {git_commit!r}
SOURCE_IDS = {source_ids_repr}
DATASET_INPUT = Path({input_dir!r})
SOURCE_SUBDIR = {source_subdir!r}
EMBEDDED_ZIP_B64_PARTS = {embedded_zip_b64_parts!r}
PAYLOAD_FILE = Path({payload_file_name!r})
WORK = Path('/kaggle/working')
OUT_DIR = WORK / 'submission_files'
OUT_DIR.mkdir(exist_ok=True)

zip_path = WORK / 'submission.zip'
used_embedded = False
payload_b64 = ''.join(EMBEDDED_ZIP_B64_PARTS)
if not payload_b64 and PAYLOAD_FILE.name and PAYLOAD_FILE.exists():
    payload_b64 = PAYLOAD_FILE.read_text().strip()
source_dir = DATASET_INPUT / SOURCE_SUBDIR
candidate_zip = DATASET_INPUT / 'submission.zip'
if candidate_zip.exists():
    shutil.copy2(candidate_zip, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    files = [n for n in names if n.endswith('.onnx')]
    used_embedded = True
elif not source_dir.exists():
    candidates = [p for p in DATASET_INPUT.rglob('task001.onnx')]
    if candidates:
        source_dir = candidates[0].parent
    elif payload_b64:
        zip_path.write_bytes(base64.b64decode(payload_b64.encode('ascii')))
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        files = [n for n in names if n.endswith('.onnx')]
        used_embedded = True
    else:
        raise FileNotFoundError(f'No task001.onnx under {{DATASET_INPUT}}')

if not used_embedded:
    files = sorted(source_dir.glob('task*.onnx'))
    if not files:
        raise FileNotFoundError(f'No task*.onnx files under {{source_dir}}')

    for src in files:
        shutil.copy2(src, OUT_DIR / src.name)

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for src in sorted(OUT_DIR.glob('task*.onnx')):
            zf.write(src, arcname=src.name)

h = hashlib.sha256()
with zip_path.open('rb') as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b''):
        h.update(chunk)

manifest = {{
    'exp_id': EXP_ID,
    'git_commit': GIT_COMMIT,
    'source_ids': SOURCE_IDS,
    'dataset_slug': {dataset_slug!r},
    'source_dir': 'embedded_zip_fallback' if used_embedded else str(source_dir),
    'package_sha256': h.hexdigest(),
    'file_count': len(files),
    'package_size': zip_path.stat().st_size,
}}
print(json.dumps(manifest, indent=2))
print('submission.zip is ready at', zip_path)
"""
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# NeuroGolf submission builder\\n",
                    f"exp_id: `{exp_id}`\\n",
                    f"dataset: `{dataset_slug}`\\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in code.strip().splitlines()],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")


def build_kernel_metadata(path: Path, notebook_name: str, dataset_sources: list[str]) -> None:
    meta = {
        "id": "muelsyse111/neurogolf-submit-current",
        "title": "NeuroGolf Submit Current",
        "code_file": notebook_name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": dataset_sources,
        "competition_sources": ["neurogolf-2026"],
        "model_sources": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
