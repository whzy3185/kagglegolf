from __future__ import annotations

from datetime import datetime
from pathlib import Path


def now_stamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def append_block(path: Path, block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(existing.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")

