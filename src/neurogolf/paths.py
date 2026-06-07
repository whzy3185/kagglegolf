from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DIRS = [
    "configs",
    "data/raw",
    "data/interim",
    "data/processed",
    "data/external",
    "data/manifests",
    "external/arc_gen",
    "external/re_arc",
    "external/arc_dsl",
    "external/public_notebooks",
    "external/public_repos",
    "external/papers",
    "src/neurogolf",
    "scripts",
    "notebooks",
    "submissions/candidates",
    "submissions/submitted",
    "submissions/failed",
    "submissions/best",
    "task_bank/tasks",
    "experiments",
    "research",
    "reports",
    "tools/kaggle",
    "tools/onnx",
    "tools/arc",
]


def root(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


def ensure_dirs() -> None:
    for rel in DIRS:
        root(rel).mkdir(parents=True, exist_ok=True)


def touch_gitkeep() -> None:
    for rel in [
        "data/raw",
        "data/interim",
        "data/processed",
        "data/external",
        "data/manifests",
        "submissions/candidates",
        "submissions/submitted",
        "submissions/failed",
        "submissions/best",
        "task_bank/tasks",
    ]:
        keep = root(rel, ".gitkeep")
        keep.parent.mkdir(parents=True, exist_ok=True)
        keep.touch(exist_ok=True)

