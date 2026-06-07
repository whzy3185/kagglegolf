from __future__ import annotations

import json
import zipfile
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root


def build_manifest(data_dir: Path) -> list[dict]:
    rows = []
    for path in sorted(data_dir.rglob("*")):
        if path.is_file():
            rows.append(
                {
                    "path": str(path.relative_to(data_dir)).replace("\\", "/"),
                    "size_bytes": path.stat().st_size,
                }
            )
    return rows


def main() -> None:
    raw = root("data/raw")
    raw.mkdir(parents=True, exist_ok=True)
    result = run_kaggle(["competitions", "download", "-c", "neurogolf-2026", "-p", str(raw), "--force"], cwd=ROOT, timeout=180)
    zip_path = raw / "neurogolf-2026.zip"
    extract_dir = raw / "neurogolf-2026"
    if zip_path.exists():
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
        manifest = {
            "download_command_output": result.stdout,
            "zip_path": str(zip_path),
            "extract_dir": str(extract_dir),
            "files": build_manifest(extract_dir),
        }
    else:
        manifest = {
            "download_command_output": result.stdout,
            "blocked": True,
            "fix": "Run kaggle auth login or accept competition rules, then rerun this script.",
        }
    out = root("data/manifests/official_files_manifest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()

