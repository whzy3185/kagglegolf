from __future__ import annotations

from pathlib import Path

from .kaggle_api import run_kaggle
from .spec import COMPETITION_SLUG


def fetch_leaderboard_text(root: Path) -> str:
    result = run_kaggle(["competitions", "leaderboard", "-c", COMPETITION_SLUG, "--show"], cwd=root, timeout=90)
    return result.stdout or ""

