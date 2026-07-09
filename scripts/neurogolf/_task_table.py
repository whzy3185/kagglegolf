from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib
import json
import math
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import traceback
import warnings
import zipfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "neurogolf_task_table"
REPORT_DIR = DATA_DIR / "reports"
FAILURE_DIR = DATA_DIR / "failures"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
DB_PATH = DATA_DIR / "neurogolf_tasks.sqlite"
RAW_TASK_DIR = ROOT / "data" / "raw" / "neurogolf-2026"
OFFICIAL_UTILS = RAW_TASK_DIR / "neurogolf_utils"
TASK_COUNT = 400
TASK_FIELDS = [
    "task_num",
    "task_id",
    "arc_task_id",
    "task_name",
    "current_onnx_path",
    "onnx_exists",
    "onnx_sha256",
    "onnx_file_size_bytes",
    "params",
    "memory_bytes",
    "macs",
    "total_cost",
    "current_score",
    "correctness",
    "verify_error",
    "train_pass",
    "train_total",
    "test_pass",
    "test_total",
    "arcgen_pass",
    "arcgen_total",
    "python_solver_pass",
    "python_solver_total",
    "onnx_pass",
    "onnx_total",
    "official_verify_status",
    "public_score",
    "target_score",
    "gap_to_target",
    "best_known_score",
    "best_known_source",
    "candidate_id",
    "source_type",
    "solver_source_path",
    "compiler_source_path",
    "rule_status",
    "rule_summary",
    "first_fail_case",
    "fail_reason",
    "failure_type",
    "recoverability",
    "onnx_template_candidate",
    "estimated_gain",
    "priority",
    "safe_to_submit",
    "last_scored_at",
    "last_updated_at",
    "notes",
]

NUMERIC_FIELDS = {
    "task_num",
    "onnx_file_size_bytes",
    "params",
    "memory_bytes",
    "macs",
    "total_cost",
    "current_score",
    "train_pass",
    "train_total",
    "test_pass",
    "test_total",
    "arcgen_pass",
    "arcgen_total",
    "python_solver_pass",
    "python_solver_total",
    "onnx_pass",
    "onnx_total",
    "public_score",
    "target_score",
    "gap_to_target",
    "best_known_score",
    "estimated_gain",
    "priority",
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def rel(path: Path | str | None) -> str:
    if not path:
        return ""
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


def ensure_dirs() -> None:
    for path in [DATA_DIR, REPORT_DIR, FAILURE_DIR, SNAPSHOT_DIR, ROOT / "scripts" / "neurogolf"]:
        path.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    ensure_dirs()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def create_schema(con: sqlite3.Connection) -> None:
    parts = []
    for field in TASK_FIELDS:
        if field == "task_num":
            parts.append("task_num INTEGER PRIMARY KEY")
        elif field in NUMERIC_FIELDS:
            parts.append(f"{field} REAL")
        else:
            parts.append(f"{field} TEXT")
    con.execute(f"CREATE TABLE IF NOT EXISTS tasks ({', '.join(parts)})")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS score_runs (
            candidate_id TEXT,
            scored_at TEXT,
            input_path TEXT,
            scoring_status TEXT,
            total_score REAL,
            pass_count INTEGER,
            fail_count INTEGER,
            missing_count INTEGER,
            warnings TEXT
        )
        """
    )
    con.commit()


def build_arc_mapping() -> tuple[dict[str, str], list[str]]:
    warnings: list[str] = []
    official = ROOT / "external" / "arc_agi_official" / "data" / "training"
    if not official.exists():
        warnings.append(f"ARC official training dir missing: {rel(official)}")
        return {}, warnings

    def canonical(payload: dict) -> str:
        text = json.dumps(
            {"train": payload.get("train", []), "test": payload.get("test", [])},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    by_hash: dict[str, str] = {}
    for path in official.glob("*.json"):
        try:
            by_hash[canonical(json.loads(path.read_text(encoding="utf-8")))] = path.stem
        except Exception as exc:
            warnings.append(f"failed ARC hash {rel(path)}: {type(exc).__name__}")
    mapping: dict[str, str] = {}
    for i in range(1, TASK_COUNT + 1):
        task_id = f"task{i:03d}"
        path = RAW_TASK_DIR / f"{task_id}.json"
        try:
            mapping[task_id] = by_hash.get(canonical(json.loads(path.read_text(encoding="utf-8"))), "")
        except Exception:
            mapping[task_id] = ""
    if any(not v for v in mapping.values()):
        warnings.append("Some task -> ARC task ids are unresolved")
    return mapping, warnings


def init_task_rows() -> list[str]:
    ensure_dirs()
    con = connect()
    create_schema(con)
    mapping, warnings = build_arc_mapping()
    stamp = now_iso()
    for i in range(1, TASK_COUNT + 1):
        task_id = f"task{i:03d}"
        row = {field: "" for field in TASK_FIELDS}
        row.update(
            {
                "task_num": i,
                "task_id": task_id,
                "arc_task_id": mapping.get(task_id, ""),
                "task_name": "",
                "onnx_exists": "false",
                "correctness": "unknown",
                "target_score": 25.0,
                "best_known_source": "unknown",
                "source_type": "unknown",
                "rule_status": "unknown",
                "failure_type": "unknown",
                "recoverability": "unknown",
                "onnx_template_candidate": "not_obvious",
                "safe_to_submit": "unknown",
                "last_updated_at": stamp,
            }
        )
        placeholders = ", ".join("?" for _ in TASK_FIELDS)
        con.execute(
            f"INSERT OR IGNORE INTO tasks ({', '.join(TASK_FIELDS)}) VALUES ({placeholders})",
            [row.get(field, "") for field in TASK_FIELDS],
        )
        con.execute(
            "UPDATE tasks SET arc_task_id = ?, last_updated_at = ? WHERE task_id = ?",
            (mapping.get(task_id, ""), stamp, task_id),
        )
    con.commit()
    count = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count != TASK_COUNT:
        raise SystemExit(f"task table has {count} rows, expected {TASK_COUNT}")
    export_scoreboard(con)
    write_fetch_log("init", "task table initialized", warnings)
    return warnings


def read_tasks(con: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = [dict(row) for row in con.execute("SELECT * FROM tasks ORDER BY task_num").fetchall()]
    if len(rows) != TASK_COUNT:
        raise SystemExit(f"task table has {len(rows)} rows, expected {TASK_COUNT}")
    return rows


def as_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except Exception:
        return default


def as_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0].keys()) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(f, "")).replace("|", "/") for f in fields) + " |")
    return "\n".join(lines)


def export_scoreboard(con: sqlite3.Connection | None = None) -> dict[str, Any]:
    own = con is None
    con = con or connect()
    rows = read_tasks(con)
    write_csv(DATA_DIR / "task_scoreboard.csv", rows, TASK_FIELDS)
    fields = [
        "task_id",
        "arc_task_id",
        "current_score",
        "target_score",
        "gap_to_target",
        "total_cost",
        "params",
        "memory_bytes",
        "macs",
        "correctness",
        "source_type",
        "candidate_id",
        "failure_type",
        "recoverability",
        "onnx_template_candidate",
        "estimated_gain",
        "priority",
    ]
    sorted_rows = sorted(rows, key=lambda r: as_float(r.get("gap_to_target"), -1), reverse=True)
    (DATA_DIR / "task_scoreboard.md").write_text("# NeuroGolf Task Scoreboard\n\n" + md_table(sorted_rows, fields), encoding="utf-8")
    render_html(sorted_rows)
    summary = scoreboard_summary(rows)
    if own:
        con.close()
    return summary


def scoreboard_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    current_total = sum(as_float(r.get("current_score")) for r in rows)
    target_total = sum(as_float(r.get("target_score")) for r in rows)
    pass_count = sum(1 for r in rows if r.get("correctness") == "pass")
    fail_count = sum(1 for r in rows if r.get("correctness") == "fail")
    missing_count = sum(1 for r in rows if r.get("onnx_exists") != "true")
    return {
        "current_total_score": current_total,
        "average_score": current_total / TASK_COUNT,
        "target_total_score": target_total,
        "total_gap": target_total - current_total,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "missing_count": missing_count,
    }


def render_html(rows: list[dict[str, Any]]) -> None:
    summary = scoreboard_summary(rows)
    cards = []
    fields = [
        "task_id",
        "arc_task_id",
        "task_name",
        "current_score",
        "target_score",
        "gap_to_target",
        "total_cost",
        "params",
        "memory_bytes",
        "macs",
        "correctness",
        "train_pass",
        "train_total",
        "test_pass",
        "test_total",
        "arcgen_pass",
        "arcgen_total",
        "python_solver_pass",
        "python_solver_total",
        "onnx_pass",
        "onnx_total",
        "source_type",
        "candidate_id",
        "failure_type",
        "recoverability",
        "onnx_template_candidate",
        "estimated_gain",
        "priority",
        "current_onnx_path",
        "notes",
    ]
    for row in rows:
        cls = "pass" if row.get("correctness") == "pass" else "fail" if row.get("correctness") == "fail" else "missing"
        if row.get("onnx_exists") != "true":
            cls = "missing"
        task_id = str(row.get("task_id", ""))
        searchable = " ".join(str(row.get(f, "")) for f in fields).lower()
        score = as_float(row.get("current_score"))
        gap = as_float(row.get("gap_to_target"))
        cost = as_float(row.get("total_cost"))
        priority = as_float(row.get("priority"))
        title = (
            f"<div class='card-title'><span>{html.escape(task_id)}</span>"
            f"<span class='pill'>{score:.4f}</span></div>"
        )
        body = "".join(
            f"<div><b>{html.escape(f)}</b>: {html.escape(str(row.get(f, '')))}</div>"
            for f in fields
        )
        cards.append(
            "<section "
            f"class='card {cls}' "
            f"data-task='{html.escape(task_id)}' "
            f"data-status='{html.escape(cls)}' "
            f"data-score='{score:.8f}' "
            f"data-gap='{gap:.8f}' "
            f"data-cost='{cost:.8f}' "
            f"data-priority='{priority:.8f}' "
            f"data-search='{html.escape(searchable)}'>"
            f"{title}{body}</section>"
        )
    style = """<style>
:root{color-scheme:light}
*{box-sizing:border-box}
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f6f7f9;color:#111}
header{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #d7dce2;padding:16px 20px}
h1{font-size:22px;margin:0 0 12px}
.summary{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:8px;margin-bottom:12px}
.metric,.card{background:#fff;border:1px solid #ddd;border-radius:6px;padding:10px}
.metric{min-height:64px}.metric span{display:block;color:#5b6470;font-size:12px}.metric b{font-size:18px}
.toolbar{display:grid;grid-template-columns:minmax(220px,1fr) 150px 170px 130px;gap:8px}
input,select,button{border:1px solid #c8ced6;border-radius:6px;background:#fff;color:#111;padding:8px 10px;font:inherit}
button{cursor:pointer}
main{padding:16px 20px}
.links{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px;font-size:13px}
.links a{color:#1459a8;text-decoration:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px}
.card{overflow:hidden}.card-title{display:flex;align-items:center;justify-content:space-between;font-weight:700;margin-bottom:8px}
.pill{border-radius:999px;background:#eef3f8;padding:2px 8px;font-size:12px}
.fail{border-color:#c62828;background:#fff4f4}.missing{border-color:#777;background:#f0f0f0}
.pass{border-color:#2e7d32}.card b{display:inline-block;min-width:150px;color:#5b6470}
.hidden{display:none!important}
@media(max-width:900px){.summary{grid-template-columns:repeat(2,1fr)}.toolbar{grid-template-columns:1fr}.grid{grid-template-columns:1fr}}
</style>"""
    script = """<script>
const cards=[...document.querySelectorAll('.card')];
const q=document.querySelector('#q');
const status=document.querySelector('#status');
const sort=document.querySelector('#sort');
const count=document.querySelector('#visible-count');
function val(card,key){ return Number(card.dataset[key] || 0); }
function apply(){
  const needle=q.value.trim().toLowerCase();
  const wanted=status.value;
  let visible=0;
  cards.forEach(card=>{
    const okText=!needle || card.dataset.search.includes(needle);
    const okStatus=!wanted || card.dataset.status===wanted;
    const show=okText && okStatus;
    card.classList.toggle('hidden', !show);
    if(show) visible++;
  });
  const grid=document.querySelector('.grid');
  const sorted=cards.slice().sort((a,b)=>{
    if(sort.value==='task') return a.dataset.task.localeCompare(b.dataset.task);
    return val(b, sort.value)-val(a, sort.value);
  });
  sorted.forEach(card=>grid.appendChild(card));
  count.textContent=visible;
}
q.addEventListener('input', apply);
status.addEventListener('change', apply);
sort.addEventListener('change', apply);
document.querySelector('#refresh').addEventListener('click', ()=>location.reload());
apply();
setTimeout(()=>location.reload(), 30000);
</script>"""
    updated = now_iso()
    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>NeuroGolf Task Scoreboard</title>{style}</head><body>
<header>
<h1>NeuroGolf Task Scoreboard</h1>
<div class="summary">
<div class="metric"><span>current_total_score</span><b>{summary['current_total_score']:.4f}</b></div>
<div class="metric"><span>average_score</span><b>{summary['average_score']:.4f}</b></div>
<div class="metric"><span>target_total_score</span><b>{summary['target_total_score']:.4f}</b></div>
<div class="metric"><span>total_gap</span><b>{summary['total_gap']:.4f}</b></div>
<div class="metric"><span>pass/fail/missing</span><b>{summary['pass_count']}/{summary['fail_count']}/{summary['missing_count']}</b></div>
<div class="metric"><span>visible/updated</span><b><span id="visible-count">{len(rows)}</span> / {updated}</b></div>
</div>
<div class="toolbar">
<input id="q" placeholder="Search task id, source, candidate, notes">
<select id="status"><option value="">All statuses</option><option value="pass">pass</option><option value="fail">fail</option><option value="missing">missing</option></select>
<select id="sort"><option value="gap">Sort: gap desc</option><option value="priority">Sort: priority desc</option><option value="cost">Sort: cost desc</option><option value="score">Sort: score desc</option><option value="task">Sort: task id</option></select>
<button id="refresh" type="button">Refresh now</button>
</div>
</header>
<main>
<div class="links">
<a href="task_scoreboard.csv">task_scoreboard.csv</a>
<a href="task_scoreboard.md">task_scoreboard.md</a>
<a href="reports/TASK_SCOREBOARD_SUMMARY.md">summary</a>
<a href="reports/NEXT_REPLACEMENT_PLAN.md">next replacement plan</a>
<span>Auto-refreshes every 30 seconds while the local watcher updates files.</span>
</div>
<div class="grid">{''.join(cards)}</div>
</main>{script}</body></html>"""
    (DATA_DIR / "task_scoreboard.html").write_text(doc, encoding="utf-8")


def write_fetch_log(candidate_id: str, message: str, warnings: list[str] | None = None) -> None:
    ensure_dirs()
    path = DATA_DIR / "FETCH_AND_SCORE_LOG.md"
    lines = []
    if path.exists():
        lines.append(path.read_text(encoding="utf-8"))
    lines.append(f"\n## {now_iso()} {candidate_id}\n\n{message}\n")
    for warning in warnings or []:
        lines.append(f"- warning: {warning}\n")
    path.write_text("".join(lines), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_input(path_arg: str) -> tuple[Path, tempfile.TemporaryDirectory[str] | None, list[str]]:
    warnings: list[str] = []
    path = ROOT / path_arg if not Path(path_arg).is_absolute() else Path(path_arg)
    if not path.exists() and path_arg.replace("\\", "/").rstrip("/") == "submissions/current":
        manifest = ROOT / "submissions" / "best" / "current_best_manifest.json"
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            exp_id = data.get("exp_id", "")
            fallback = ROOT / "submissions" / "candidates" / exp_id / "onnx"
            if fallback.exists():
                warnings.append(f"{path_arg} missing; using {rel(fallback)}")
                return fallback, None, warnings
            zip_fallback = ROOT / "submissions" / "candidates" / exp_id / "submission.zip"
            if zip_fallback.exists():
                warnings.append(f"{path_arg} missing; using {rel(zip_fallback)}")
                path = zip_fallback
    if path.is_file() and path.suffix.lower() == ".zip":
        tmp = tempfile.TemporaryDirectory(prefix="neurogolf_score_")
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp.name)
        root = Path(tmp.name)
        dirs = [p for p in [root, *root.rglob("*")] if p.is_dir() and list(p.glob("task*.onnx"))]
        if not dirs:
            raise SystemExit(f"No task*.onnx found in {path}")
        return dirs[0], tmp, warnings
    if path.is_dir():
        if (path / "onnx").is_dir():
            path = path / "onnx"
        return path, None, warnings
    raise SystemExit(f"Input path does not exist or is unsupported: {path_arg}")


def load_official_utils() -> tuple[Any | None, str]:
    if not OFFICIAL_UTILS.exists():
        return None, f"official utils missing: {rel(OFFICIAL_UTILS)}"
    sys.path.insert(0, str(OFFICIAL_UTILS))
    try:
        mod = importlib.import_module("neurogolf_utils")
        mod._NEUROGOLF_DIR = str(RAW_TASK_DIR).replace("\\", "/") + "/"
        return mod, "official neurogolf_utils"
    except Exception as exc:
        return None, f"official utils import failed: {type(exc).__name__}: {exc}"


def load_task_json(task_id: str) -> dict:
    return json.loads((RAW_TASK_DIR / f"{task_id}.json").read_text(encoding="utf-8"))


def fallback_convert_to_numpy(example: dict) -> dict[str, Any] | None:
    import numpy as np

    out: dict[str, Any] = {}
    for mode in ["input", "output"]:
        grid = example.get(mode)
        if not grid or not grid[0] or max(len(grid), len(grid[0])) > 30:
            return None
        arr = np.zeros((1, 10, 30, 30), dtype=np.float32)
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                arr[0, int(color), r, c] = 1.0
        out[mode] = arr
    return out


def compact_array(value: Any, limit: int = 500) -> str:
    try:
        text = json.dumps(value, separators=(",", ":"))
    except Exception:
        text = str(value)
    return text[:limit]


def classify_failure(error: str, expected: Any = None, actual: Any = None) -> str:
    low = (error or "").lower()
    if "shape" in low or "dimension" in low or "broadcast" in low:
        return "broadcast_shape_error"
    if "type" in low or "invalidargument" in low:
        return "onnx_type_error"
    if "dynamic" in low or "dim_param" in low:
        return "dynamic_shape_error"
    if "verify" in low or "checker" in low or "session" in low:
        return "verifier_error"
    if expected is not None and actual is not None:
        try:
            if getattr(expected, "shape", None) != getattr(actual, "shape", None):
                return "size_error"
        except Exception:
            pass
        return "color_error"
    return "unknown"


def score_one_task(onnx_path: Path | None, task_num: int, candidate_id: str, utils: Any | None, utils_status: str) -> dict[str, Any]:
    import numpy as np
    import onnx
    import onnxruntime as ort

    task_id = f"task{task_num:03d}"
    stamp = now_iso()
    row: dict[str, Any] = {field: "" for field in TASK_FIELDS}
    row.update(
        {
            "task_num": task_num,
            "task_id": task_id,
            "candidate_id": candidate_id,
            "target_score": 25.0,
            "source_type": "unknown",
            "rule_status": "unknown",
            "recoverability": "unknown",
            "onnx_template_candidate": "not_obvious",
            "safe_to_submit": "unknown",
            "last_scored_at": stamp,
            "last_updated_at": stamp,
            "macs": "",
            "notes": "",
        }
    )
    if onnx_path is None or not onnx_path.exists():
        row.update({"onnx_exists": "false", "correctness": "unknown", "official_verify_status": "missing"})
        return row

    row.update(
        {
            "current_onnx_path": rel(onnx_path),
            "onnx_exists": "true",
            "onnx_sha256": sha256_file(onnx_path),
            "onnx_file_size_bytes": onnx_path.stat().st_size,
        }
    )

    split_names = ["train", "test", "arc-gen"]
    totals = {split: 0 for split in split_names}
    passes = {split: 0 for split in split_names}
    first_fail: dict[str, Any] | None = None
    failures = 0
    total_examples = 0
    trace_path = ""
    try:
        model = onnx.load(str(onnx_path))
        onnx.checker.check_model(model, full_check=True)
        sanitized = utils.sanitize_model(onnx.load(str(onnx_path))) if utils else model
        if sanitized is None:
            raise RuntimeError("sanitize_model returned None")
        options = ort.SessionOptions()
        options.enable_profiling = True
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        options.profile_file_prefix = f"task_table_{candidate_id}_{task_id}"
        session = ort.InferenceSession(sanitized.SerializeToString(), options, providers=["CPUExecutionProvider"])
        payload = load_task_json(task_id)
        convert = utils.convert_to_numpy if utils else fallback_convert_to_numpy
        for split in split_names:
            for idx, example in enumerate(payload.get(split, [])):
                arrays = convert(example)
                if arrays is None:
                    continue
                totals[split] += 1
                total_examples += 1
                try:
                    output = session.run(["output"], {"input": arrays["input"]})[0]
                    pred = (output > 0.0).astype(np.float32)
                    ok = bool(np.array_equal(pred, arrays["output"]))
                    if ok:
                        passes[split] += 1
                    else:
                        failures += 1
                        if first_fail is None:
                            first_fail = {
                                "split": split,
                                "index": idx,
                                "failure_pixels": int(np.sum(pred != arrays["output"])),
                                "input": example.get("input"),
                                "expected": example.get("output"),
                                "actual": utils.convert_from_numpy(pred) if utils else [],
                            }
                except Exception as exc:
                    failures += 1
                    if first_fail is None:
                        first_fail = {
                            "split": split,
                            "index": idx,
                            "error": f"{type(exc).__name__}: {exc}",
                            "input": example.get("input"),
                            "expected": example.get("output"),
                            "actual": [],
                        }
        trace_path = session.end_profiling()
        memory = params = None
        if utils:
            memory, params = utils.score_network(sanitized, trace_path)
        else:
            row["verify_error"] = utils_status
        if memory is not None:
            row["memory_bytes"] = int(memory)
        if params is not None:
            row["params"] = int(params)
        if memory is not None and params is not None:
            total_cost = int(memory + params)
            row["total_cost"] = total_cost
            row["current_score"] = max(1.0, 25.0 - math.log(max(1.0, total_cost))) if failures == 0 else 0.0
        else:
            row["verify_error"] = row.get("verify_error") or "official scorer returned missing params/memory"
        row.update(
            {
                "train_pass": passes["train"],
                "train_total": totals["train"],
                "test_pass": passes["test"],
                "test_total": totals["test"],
                "arcgen_pass": passes["arc-gen"],
                "arcgen_total": totals["arc-gen"],
                "onnx_pass": total_examples - failures,
                "onnx_total": total_examples,
                "correctness": "pass" if failures == 0 else "fail",
                "official_verify_status": "pass" if failures == 0 and row.get("total_cost") != "" else "fail",
                "safe_to_submit": "true" if failures == 0 and row.get("total_cost") != "" else "false",
            }
        )
        if first_fail:
            row["first_fail_case"] = compact_array(first_fail)
            row["fail_reason"] = first_fail.get("error", "output_mismatch")
            row["failure_type"] = classify_failure(row["fail_reason"])
        else:
            row["failure_type"] = "none"
        if row.get("current_score") != "":
            row["best_known_score"] = row["current_score"]
            row["gap_to_target"] = as_float(row["target_score"], 25.0) - as_float(row["current_score"])
        return row
    except Exception as exc:
        row.update(
            {
                "correctness": "fail",
                "verify_error": f"{type(exc).__name__}: {exc}",
                "official_verify_status": "error",
                "failure_type": classify_failure(str(exc)),
                "safe_to_submit": "false",
                "current_score": 0.0,
                "gap_to_target": 25.0,
                "onnx_pass": 0,
                "onnx_total": 0,
            }
        )
        return row
    finally:
        if trace_path:
            try:
                os.remove(trace_path)
            except Exception:
                pass


def score_submission(input_path: str, candidate_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ensure_dirs()
    root, tmp, warnings = resolve_input(input_path)
    utils, utils_status = load_official_utils()
    if utils is None:
        warnings.append(utils_status)
    rows = []
    started = time.time()
    try:
        for i in range(1, TASK_COUNT + 1):
            task_id = f"task{i:03d}"
            path = root / f"{task_id}.onnx"
            try:
                rows.append(score_one_task(path if path.exists() else None, i, candidate_id, utils, utils_status))
            except Exception as exc:
                row = {field: "" for field in TASK_FIELDS}
                row.update(
                    {
                        "task_num": i,
                        "task_id": task_id,
                        "candidate_id": candidate_id,
                        "onnx_exists": "false",
                        "correctness": "fail",
                        "verify_error": f"score_task_exception:{type(exc).__name__}:{exc}",
                        "failure_type": "unknown",
                        "official_verify_status": "error",
                        "current_score": 0.0,
                        "target_score": 25.0,
                        "gap_to_target": 25.0,
                        "last_scored_at": now_iso(),
                        "last_updated_at": now_iso(),
                    }
                )
                rows.append(row)
            if i % 25 == 0:
                print(f"scored={i}/400", flush=True)
    finally:
        if tmp is not None:
            tmp.cleanup()
    summary = scoreboard_summary(rows)
    summary.update(
        {
            "candidate_id": candidate_id,
            "input_path": rel(root),
            "scored_at": now_iso(),
            "elapsed_seconds": round(time.time() - started, 3),
            "scoring_source": utils_status,
            "warnings": warnings,
        }
    )
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    json_path = SNAPSHOT_DIR / f"score_{candidate_id}_{stamp}.json"
    csv_path = SNAPSHOT_DIR / f"score_{candidate_id}_{stamp}.csv"
    json_path.write_text(json.dumps({"summary": summary, "tasks": rows}, indent=2), encoding="utf-8")
    write_csv(csv_path, rows, TASK_FIELDS)
    write_fetch_log(candidate_id, f"scored {rel(root)} total={summary['current_total_score']:.4f}", warnings)
    return rows, summary


def latest_snapshot(candidate_id: str) -> Path:
    files = sorted(SNAPSHOT_DIR.glob(f"score_{candidate_id}_*.json"))
    if not files:
        raise SystemExit(f"No score snapshot found for candidate_id={candidate_id}")
    return files[-1]


def update_task_table(candidate_id: str, snapshot: Path | None = None) -> dict[str, Any]:
    ensure_dirs()
    con = connect()
    create_schema(con)
    path = snapshot or latest_snapshot(candidate_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["tasks"]
    old_rows = {r["task_id"]: r for r in read_tasks(con)}
    history_rows = read_history()
    stamp = now_iso()
    for row in rows:
        task_id = row["task_id"]
        old = old_rows.get(task_id, {})
        old_score = as_float(old.get("current_score"), float("nan"))
        new_score = as_float(row.get("current_score"), float("nan"))
        old_cost = as_float(old.get("total_cost"), float("nan"))
        new_cost = as_float(row.get("total_cost"), float("nan"))
        target = as_float(row.get("target_score"), as_float(old.get("target_score"), 25.0))
        row["target_score"] = target
        row["gap_to_target"] = target - as_float(row.get("current_score"))
        old_best = old.get("best_known_score")
        if row.get("current_score") != "" and (old_best in (None, "") or as_float(row["current_score"]) > as_float(old_best)):
            row["best_known_score"] = row["current_score"]
            row["best_known_source"] = candidate_id
        else:
            row["best_known_score"] = old_best or row.get("current_score", "")
            row["best_known_source"] = old.get("best_known_source") or candidate_id
        row["last_updated_at"] = stamp
        values = [row.get(field, "") for field in TASK_FIELDS]
        assignments = ", ".join(f"{field}=?" for field in TASK_FIELDS if field != "task_num")
        con.execute(
            f"UPDATE tasks SET {assignments} WHERE task_num=?",
            [row.get(field, "") for field in TASK_FIELDS if field != "task_num"] + [row["task_num"]],
        )
        changed = (
            (not math.isnan(old_score) and abs(old_score - new_score) > 1e-9)
            or (not math.isnan(old_cost) and abs(old_cost - new_cost) > 1e-9)
            or old.get("candidate_id") != candidate_id
        )
        if changed:
            history_rows.append(
                {
                    "timestamp": stamp,
                    "task_id": task_id,
                    "old_score": "" if math.isnan(old_score) else old_score,
                    "new_score": "" if math.isnan(new_score) else new_score,
                    "delta": "" if math.isnan(old_score) or math.isnan(new_score) else new_score - old_score,
                    "old_cost": "" if math.isnan(old_cost) else old_cost,
                    "new_cost": "" if math.isnan(new_cost) else new_cost,
                    "candidate_id": candidate_id,
                    "notes": "score_or_cost_updated",
                }
            )
    summary = payload.get("summary", scoreboard_summary(rows))
    con.execute(
        "INSERT INTO score_runs VALUES (?,?,?,?,?,?,?,?,?)",
        (
            candidate_id,
            stamp,
            summary.get("input_path", ""),
            summary.get("scoring_source", ""),
            summary.get("current_total_score", 0.0),
            summary.get("pass_count", 0),
            summary.get("fail_count", 0),
            summary.get("missing_count", 0),
            ";".join(summary.get("warnings", [])),
        ),
    )
    con.commit()
    write_csv(DATA_DIR / "task_history.csv", history_rows, list(history_rows[0].keys()) if history_rows else ["timestamp", "task_id", "old_score", "new_score", "delta", "old_cost", "new_cost", "candidate_id", "notes"])
    export_scoreboard(con)
    write_summary_reports(con)
    con.close()
    return summary


def read_history() -> list[dict[str, Any]]:
    path = DATA_DIR / "task_history.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_summary_reports(con: sqlite3.Connection | None = None) -> None:
    own = con is None
    con = con or connect()
    rows = read_tasks(con)
    summary = scoreboard_summary(rows)
    top_gap = sorted(rows, key=lambda r: as_float(r.get("gap_to_target"), -1), reverse=True)[:50]
    top_cost = sorted(rows, key=lambda r: as_float(r.get("total_cost"), -1), reverse=True)[:50]
    low_score = sorted(rows, key=lambda r: as_float(r.get("current_score"), 1e9))[:50]
    history = read_history()
    gains = sorted(history, key=lambda r: as_float(r.get("delta"), -1), reverse=True)[:20]
    drops = sorted(history, key=lambda r: as_float(r.get("delta"), 1), reverse=False)[:20]
    priority = rank_replacement_tasks(rows)[:50]
    fields = ["task_id", "current_score", "target_score", "gap_to_target", "total_cost", "correctness", "failure_type", "recoverability", "onnx_template_candidate", "estimated_gain", "priority"]
    report = [
        "# Task Scoreboard Summary\n",
        f"updated_at: {now_iso()}\n",
        f"current_total_score: {summary['current_total_score']:.6f}\n",
        f"average_score: {summary['average_score']:.6f}\n",
        f"target_total_score: {summary['target_total_score']:.6f}\n",
        f"total_gap: {summary['total_gap']:.6f}\n",
        f"pass/fail/missing: {summary['pass_count']}/{summary['fail_count']}/{summary['missing_count']}\n",
        "\n## Top 50 Gap To Target\n",
        md_table(top_gap, fields),
        "\n## Top 50 Cost\n",
        md_table(top_cost, fields),
        "\n## Top 50 Lowest Score\n",
        md_table(low_score, fields),
        "\n## Recent Improvements\n",
        md_table(gains, ["timestamp", "task_id", "old_score", "new_score", "delta", "candidate_id"]) if gains else "None.",
        "\n## Recent Drops\n",
        md_table(drops, ["timestamp", "task_id", "old_score", "new_score", "delta", "candidate_id"]) if drops else "None.",
        "\n## Priority Replacement Tasks\n",
        md_table(priority, fields),
    ]
    (REPORT_DIR / "TASK_SCOREBOARD_SUMMARY.md").write_text("\n".join(report), encoding="utf-8")
    plan = [
        "# Next Replacement Plan\n",
        f"updated_at: {now_iso()}\n",
        "\nThe list is generated from current cost, score gap, correctness, solver-source availability and ONNX template simplicity.\n",
        md_table(priority[:30], fields + ["solver_source_path", "compiler_source_path", "rule_status", "safe_to_submit"]),
    ]
    (REPORT_DIR / "NEXT_REPLACEMENT_PLAN.md").write_text("\n".join(plan), encoding="utf-8")
    if own:
        con.close()


def infer_template(row: dict[str, Any]) -> str:
    summary = " ".join(str(row.get(k, "")).lower() for k in ["rule_summary", "notes", "solver_source_path"])
    if "conv" in summary or "neighbor" in summary:
        return "3x3_conv_neighborhood"
    if "where" in summary or "fill" in summary:
        return "onehot_where_fill"
    if "crop" in summary or "pad" in summary or "slice" in summary:
        return "slice_pad_resize"
    if "argmax" in summary or "color" in summary:
        return "reduce_argmax_color"
    if "repeat" in summary or "concat" in summary:
        return "static_repeat"
    if "object" in summary:
        return "object_tree"
    return row.get("onnx_template_candidate") or "not_obvious"


def rank_replacement_tasks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for row in rows:
        r = dict(row)
        score = as_float(r.get("current_score"))
        gap = as_float(r.get("gap_to_target"))
        cost = as_float(r.get("total_cost"))
        py_full = as_int(r.get("python_solver_pass")) and as_int(r.get("python_solver_pass")) == as_int(r.get("python_solver_total"))
        correctness_bonus = 5 if r.get("correctness") == "pass" else 8 if py_full else 0
        simple_bonus = 4 if infer_template(r) != "not_obvious" else 0
        priority = gap + math.log(max(cost, 1.0)) + correctness_bonus + simple_bonus
        r["priority"] = round(priority, 6)
        r["estimated_gain"] = round(min(gap, max(0.0, 25.0 - score)), 6)
        r["onnx_template_candidate"] = infer_template(r)
        ranked.append(r)
    return sorted(ranked, key=lambda r: as_float(r.get("priority")), reverse=True)


def render_dashboard() -> None:
    con = connect()
    export_scoreboard(con)
    write_summary_reports(con)
    con.close()


def import_targets(path_arg: str) -> list[str]:
    path = ROOT / path_arg if not Path(path_arg).is_absolute() else Path(path_arg)
    warnings: list[str] = []
    if not path.exists():
        raise SystemExit(f"target file missing: {path_arg}")
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        records = data if isinstance(data, list) else data.get("tasks", [])
    else:
        with path.open(newline="", encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
    con = connect()
    create_schema(con)
    stamp = now_iso()
    for rec in records:
        task_id = rec.get("task_id") or rec.get("task")
        if not task_id:
            warnings.append("target row missing task_id")
            continue
        if task_id.isdigit():
            task_id = f"task{int(task_id):03d}"
        source = rec.get("source") or rec.get("best_known_source") or "unknown"
        if source == "unknown":
            warnings.append(f"{task_id} target source missing")
        target = rec.get("target_score") or rec.get("best_known_score")
        best = rec.get("best_known_score") or target
        current = con.execute("SELECT current_score FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        current_score = as_float(current[0]) if current else 0.0
        gap = as_float(target, current_score) - current_score if target not in (None, "") else ""
        con.execute(
            """
            UPDATE tasks SET target_score=?, best_known_score=?, best_known_source=?,
            gap_to_target=?, notes=?, last_updated_at=? WHERE task_id=?
            """,
            (target, best, source, gap, rec.get("notes", ""), stamp, task_id),
        )
    con.commit()
    export_scoreboard(con)
    write_summary_reports(con)
    con.close()
    return warnings


def correctness_audit() -> list[dict[str, Any]]:
    con = connect()
    rows = read_tasks(con)
    audit = []
    for row in rows:
        train_full = as_int(row.get("train_pass")) == as_int(row.get("train_total")) and as_int(row.get("train_total")) > 0
        test_full = as_int(row.get("test_pass")) == as_int(row.get("test_total")) and as_int(row.get("test_total")) > 0
        arc_full = as_int(row.get("arcgen_pass")) == as_int(row.get("arcgen_total")) and as_int(row.get("arcgen_total")) > 0
        py_full = as_int(row.get("python_solver_pass")) == as_int(row.get("python_solver_total")) and as_int(row.get("python_solver_total")) > 0
        onnx_full = as_int(row.get("onnx_pass")) == as_int(row.get("onnx_total")) and as_int(row.get("onnx_total")) > 0
        rec = {
            "task_id": row.get("task_id"),
            "official_verify_status": row.get("official_verify_status"),
            "onnx_pass": row.get("onnx_pass"),
            "onnx_total": row.get("onnx_total"),
            "train_pass": row.get("train_pass"),
            "train_total": row.get("train_total"),
            "test_pass": row.get("test_pass"),
            "test_total": row.get("test_total"),
            "arcgen_pass": row.get("arcgen_pass"),
            "arcgen_total": row.get("arcgen_total"),
            "python_solver_pass": row.get("python_solver_pass"),
            "python_solver_total": row.get("python_solver_total"),
            "python_full_but_onnx_fail": str(py_full and not onnx_full).lower(),
            "train_test_full_but_arcgen_fail": str(train_full and test_full and not arc_full).lower(),
            "first_fail_case": row.get("first_fail_case"),
            "fail_reason": row.get("fail_reason"),
            "failure_type": row.get("failure_type"),
            "current_score": row.get("current_score"),
            "total_cost": row.get("total_cost"),
            "suggested_fix": suggested_fix(row),
        }
        audit.append(rec)
    fields = list(audit[0].keys()) if audit else []
    write_csv(DATA_DIR / "correctness_audit.csv", audit, fields)
    bad = [r for r in audit if r["official_verify_status"] != "pass"]
    (DATA_DIR / "correctness_audit.md").write_text("# Correctness Audit\n\n" + md_table(audit, fields), encoding="utf-8")
    report = [
        "# Correctness Failures\n",
        f"updated_at: {now_iso()}\n",
        f"not_full_pass_count: {len(bad)}\n",
        "\n## Non Full-Pass Tasks\n",
        md_table(bad, fields) if bad else "None.",
        "\n## Python Full Pass But ONNX Fail\n",
        md_table([r for r in audit if r["python_full_but_onnx_fail"] == "true"], fields) or "None.",
        "\n## Train/Test Full But ARC-GEN Fail\n",
        md_table([r for r in audit if r["train_test_full_but_arcgen_fail"] == "true"], fields) or "None.",
        "\n## Top 30 Repair Candidates\n",
        md_table(sorted(bad, key=lambda r: as_float(r.get("total_cost")), reverse=True)[:30], fields) if bad else "None.",
    ]
    (REPORT_DIR / "CORRECTNESS_FAILURES.md").write_text("\n".join(report), encoding="utf-8")
    con.close()
    return audit


def suggested_fix(row: dict[str, Any]) -> str:
    ft = row.get("failure_type")
    if ft in {"broadcast_shape_error", "dynamic_shape_error"}:
        return "fix static shape / Slice-Pad boundary logic"
    if ft == "connectivity_error":
        return "replace with 3x3_conv_neighborhood or object_tree"
    if ft in {"color_error", "background_fill_error"}:
        return "check onehot_where_fill and background channel"
    if row.get("correctness") == "pass" and as_float(row.get("total_cost")) > 50000:
        return "memory-first ONNX surgery"
    return "inspect rule and source solver"


def as_grid(value: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(c) for c in row) for row in value)


def run_grid_solver(
    func: Any,
    task_payload: dict,
    limit_arcgen: int = 0,
    max_examples: int = 40,
) -> tuple[int, int, int, str]:
    passed = total = 0
    expected_total = sum(len(task_payload.get(split, [])) for split in ["train", "test", "arc-gen"])
    errors = []
    for split in ["train", "test", "arc-gen"]:
        examples = task_payload.get(split, [])
        if split == "arc-gen" and limit_arcgen:
            examples = examples[:limit_arcgen]
        for idx, ex in enumerate(examples):
            if max_examples and total >= max_examples:
                errors.append(f"sampled_public_solver_examples={max_examples};expected_total={expected_total}")
                return passed, total, expected_total, ";".join(errors)
            total += 1
            try:
                out = func(as_grid(ex["input"]))
                norm = json.loads(json.dumps(out))
                if norm == ex["output"]:
                    passed += 1
                elif len(errors) < 3:
                    errors.append(f"{split}[{idx}]:mismatch")
            except Exception as exc:
                if len(errors) < 3:
                    errors.append(f"{split}[{idx}]:{type(exc).__name__}")
    return passed, total, expected_total, ";".join(errors)


def failed_task_recovery_audit() -> list[dict[str, Any]]:
    con = connect()
    rows = read_tasks(con)
    mapping, warnings = build_arc_mapping()
    arc_solvers = None
    arc_path = ROOT / "external" / "arc_dsl"
    if arc_path.exists():
        sys.path.insert(0, str(arc_path))
        try:
            arc_solvers = importlib.import_module("solvers")
        except Exception as exc:
            warnings.append(f"ARC-DSL import failed: {type(exc).__name__}: {exc}")
    cgi_dir = ROOT / "external" / "public_repos" / "NeurIPS-Code-Golf-2025" / "solutions"
    records = []
    stamp = now_iso()
    for row in rows:
        task_id = row["task_id"]
        task_num = int(task_id[4:])
        payload = load_task_json(task_id)
        arc_id = mapping.get(task_id, row.get("arc_task_id", ""))
        rec = {
            "task_id": task_id,
            "arc_task_id": arc_id,
            "current_score": row.get("current_score"),
            "total_cost": row.get("total_cost"),
            "correctness": row.get("correctness"),
            "gap_to_target": row.get("gap_to_target"),
            "arc_dsl_exists": "false",
            "arc_dsl_solver_path": "",
            "arc_dsl_python_pass": "",
            "arc_dsl_python_total": "",
            "cgi_exists": "false",
            "cgi_solver_path": "",
            "cgi_python_pass": "",
            "cgi_python_total": "",
            "other_source": "",
            "other_source_path": "",
            "other_source_pass_total": "",
            "category": "",
            "recommended_source": "",
            "recommended_onnx_template": infer_template(row),
            "priority": "",
            "notes": "",
        }
        arc_full = False
        if arc_solvers and arc_id:
            solver = getattr(arc_solvers, f"solve_{arc_id}", None)
            if solver:
                rec["arc_dsl_exists"] = "true"
                rec["arc_dsl_solver_path"] = rel(arc_path / "solvers.py")
                p, t, expected_t, err = run_grid_solver(solver, payload)
                rec["arc_dsl_python_pass"] = p
                rec["arc_dsl_python_total"] = t
                arc_full = p == t and t > 0 and t == expected_t
                if err:
                    rec["notes"] = err
        cgi_path = cgi_dir / f"{task_id}.py"
        cgi_full = False
        if cgi_path.exists():
            rec["cgi_exists"] = "true"
            rec["cgi_solver_path"] = rel(cgi_path)
            try:
                scope: dict[str, Any] = {}
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    exec(cgi_path.read_text(encoding="utf-8"), scope)
                solver = scope.get("p")
                if solver:
                    p, t, expected_t, err = run_grid_solver(solver, payload)
                    rec["cgi_python_pass"] = p
                    rec["cgi_python_total"] = t
                    cgi_full = p == t and t > 0 and t == expected_t
                    if err and not rec["notes"]:
                        rec["notes"] = err
            except Exception as exc:
                rec["notes"] = rec["notes"] or f"cgi_error:{type(exc).__name__}"
        if row.get("correctness") != "pass":
            if arc_full and not cgi_full:
                category = "ARC-DSL solver passes but current ONNX fails"
                source = "ARC-DSL"
            elif cgi_full and not arc_full:
                category = "CGI solver passes but current ONNX fails"
                source = "CGI Code Golf"
            elif arc_full and cgi_full:
                category = "Python solvers pass but ONNX needs compile"
                source = "ARC-DSL / CGI Code Golf"
            else:
                category = "rule unknown or public solvers fail"
                source = "rule discovery"
        elif as_float(row.get("total_cost")) > 50000:
            category = "ONNX passes but cost too high"
            source = "memory-first ONNX surgery"
        elif arc_full or cgi_full:
            category = "public solver available for future compression"
            source = "ARC-DSL" if arc_full else "CGI Code Golf"
        else:
            category = "currently OK; no immediate recovery need"
            source = "current ONNX"
        rec["category"] = category
        rec["recommended_source"] = source
        priority = as_float(row.get("gap_to_target")) + math.log(max(as_float(row.get("total_cost")), 1))
        if arc_full or cgi_full:
            priority += 8
        if rec["recommended_onnx_template"] != "not_obvious":
            priority += 3
        rec["priority"] = round(priority, 6)
        records.append(rec)
        con.execute(
            """
            UPDATE tasks SET arc_task_id=?, python_solver_pass=?, python_solver_total=?, solver_source_path=?,
            onnx_template_candidate=?, recoverability=?, priority=?, estimated_gain=?,
            last_updated_at=? WHERE task_id=?
            """,
            (
                arc_id,
                rec["arc_dsl_python_pass"] or rec["cgi_python_pass"],
                rec["arc_dsl_python_total"] or rec["cgi_python_total"],
                rec["arc_dsl_solver_path"] or rec["cgi_solver_path"],
                rec["recommended_onnx_template"],
                infer_recoverability(rec, row),
                rec["priority"],
                min(as_float(row.get("gap_to_target")), max(0.0, 25.0 - as_float(row.get("current_score")))),
                stamp,
                task_id,
            ),
        )
    con.commit()
    export_scoreboard(con)
    write_summary_reports(con)
    con.close()
    write_recovery_report(records, warnings)
    return records


def infer_recoverability(rec: dict[str, Any], row: dict[str, Any]) -> str:
    if rec["category"].startswith("currently OK") and as_float(row.get("total_cost")) < 40000:
        return "unknown"
    if rec.get("recommended_onnx_template") != "not_obvious" and (rec["arc_dsl_exists"] == "true" or rec["cgi_exists"] == "true"):
        return "easy"
    if rec["arc_dsl_exists"] == "true" or rec["cgi_exists"] == "true":
        return "medium"
    if row.get("correctness") == "pass":
        return "medium"
    return "hard"


def write_recovery_report(records: list[dict[str, Any]], warnings: list[str]) -> None:
    fields = list(records[0].keys()) if records else []
    write_csv(FAILURE_DIR / "failed_task_recovery_audit.csv", records, fields)
    ranked = sorted(records, key=lambda r: as_float(r.get("priority")), reverse=True)
    easy = [r for r in ranked if r.get("category") != "currently OK; no immediate recovery need"][:30]
    py_full_onnx_fail = [
        r for r in ranked
        if (
            (as_int(r.get("arc_dsl_python_pass")) == as_int(r.get("arc_dsl_python_total")) and as_int(r.get("arc_dsl_python_total")) > 0)
            or (as_int(r.get("cgi_python_pass")) == as_int(r.get("cgi_python_total")) and as_int(r.get("cgi_python_total")) > 0)
        )
    ]
    high_cost = [r for r in ranked if as_float(r.get("total_cost")) > 50000]
    report = [
        "# Failed Task Recovery Audit\n",
        f"updated_at: {now_iso()}\n",
        "\n## Reliability Notes\n",
    ]
    if warnings:
        report.extend(f"- {w}" for w in warnings)
    else:
        report.append("- official/local solver sources loaded where available")
    report.extend(
        [
            "\n## Easiest Top 30 Recovery / Compression Tasks\n",
            md_table(easy, fields) if easy else "None.",
            "\n## Python Full Pass But ONNX Not Yet Promoted / Needs Compile\n",
            md_table(py_full_onnx_fail[:50], fields) if py_full_onnx_fail else "None.",
            "\n## Current High-Cost But Rule-Simple Tasks\n",
            md_table(high_cost[:50], fields) if high_cost else "None.",
            "\n## Not Recommended Short-Term / Complex Tasks\n",
            md_table([r for r in ranked if r.get("recommended_onnx_template") == "not_obvious"][:50], fields) or "None.",
        ]
    )
    (REPORT_DIR / "FAILED_TASK_RECOVERY_AUDIT.md").write_text("\n".join(report), encoding="utf-8")


def watch_and_refresh(input_path: str, candidate_id: str, interval: int = 30, once: bool = False) -> None:
    last_state: dict[str, float] = {}
    while True:
        root, tmp, warnings = resolve_input(input_path)
        try:
            files = list(root.glob("task*.onnx"))
            if (ROOT / input_path).suffix.lower() == ".zip":
                files = [ROOT / input_path]
            state = {str(p): p.stat().st_mtime for p in files}
        finally:
            if tmp is not None:
                tmp.cleanup()
        if state != last_state:
            rows, summary = score_submission(input_path, candidate_id)
            update_task_table(candidate_id)
            render_dashboard()
            correctness_audit()
            failed_task_recovery_audit()
            write_fetch_log(candidate_id, f"watch refresh changed={len(state)} total={summary['current_total_score']:.4f}", warnings)
            last_state = state
        if once:
            break
        time.sleep(interval)


def print_quality_query() -> None:
    con = connect()
    print("task_count=", con.execute("select count(*) from tasks").fetchone()[0])
    print("score_sum=", con.execute("select sum(current_score) from tasks").fetchone()[0])
    print("top_gap=", con.execute("select task_id,current_score,target_score,gap_to_target,total_cost from tasks order by gap_to_target desc limit 20").fetchall())
    print("top_cost=", con.execute("select task_id,current_score,total_cost,correctness from tasks order by total_cost desc limit 20").fetchall())
    print("lowest_score=", con.execute("select task_id,current_score,total_cost,correctness from tasks order by current_score asc limit 20").fetchall())
    con.close()
