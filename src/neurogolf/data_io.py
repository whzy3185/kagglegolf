from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np

from . import spec
from .paths import root


def official_data_dir() -> Path:
    local = root("data/raw/neurogolf-2026")
    if local.exists():
        return local
    kaggle = Path("/kaggle/input/competitions/neurogolf-2026")
    if kaggle.exists():
        return kaggle
    return local


def task_paths(data_dir: Path | None = None) -> list[Path]:
    data_dir = data_dir or official_data_dir()
    return sorted(data_dir.glob("task*.json"))


def task_id_from_path(path: Path) -> str:
    return path.stem


def load_task(path_or_task: Path | str, data_dir: Path | None = None) -> dict:
    if isinstance(path_or_task, Path):
        path = path_or_task
    else:
        name = path_or_task if path_or_task.endswith(".json") else f"{path_or_task}.json"
        path = (data_dir or official_data_dir()) / name
    return json.loads(path.read_text(encoding="utf-8"))


def iter_pairs(task: dict, splits: Iterable[str] = ("train", "test", "arc-gen")):
    for split in splits:
        for pair in task.get(split, []):
            yield split, pair


def grid_to_onehot(grid: list[list[int]]) -> np.ndarray | None:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    if max(height, width) > 30:
        return None
    arr = np.zeros(spec.TENSOR_SHAPE, dtype=np.float32)
    for r, row in enumerate(grid):
        if len(row) != width:
            return None
        for c, color in enumerate(row):
            if not isinstance(color, int) or color < 0 or color > 9:
                return None
            arr[0, color, r, c] = 1.0
    return arr


def pair_to_numpy(pair: dict) -> tuple[np.ndarray, np.ndarray] | None:
    x = grid_to_onehot(pair["input"])
    y = grid_to_onehot(pair["output"])
    if x is None or y is None:
        return None
    return x, y


def exact_onehot_equal(raw_output: np.ndarray, expected: np.ndarray) -> bool:
    pred = (raw_output > 0.0).astype(np.float32)
    return bool(np.array_equal(pred, expected))

