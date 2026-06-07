from __future__ import annotations

import subprocess
from pathlib import Path


def run_kaggle(args: list[str], cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["kaggle", *args],
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def command_text(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout or ""

