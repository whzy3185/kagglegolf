from __future__ import annotations

from pathlib import Path


def copy_as_rewrite(source: Path, target: Path) -> None:
    """Placeholder rewrite lane: keep API stable while real graph surgery is added."""
    import shutil

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

