from __future__ import annotations

import subprocess


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    commit = result.stdout.strip()
    return commit or "uncommitted"

