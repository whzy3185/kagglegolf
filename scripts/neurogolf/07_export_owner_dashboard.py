from __future__ import annotations

import argparse
import csv
import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_TABLE = ROOT / "data" / "neurogolf_task_table" / "task_scoreboard.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(f, "")).replace("|", "/") for f in fields) + " |")
    return "\n".join(lines)


def render_owner_html(owner: str, rows: list[dict[str, Any]], out: Path) -> None:
    total_score = sum(as_float(r.get("current_score")) for r in rows)
    total_gap = sum(as_float(r.get("gap_to_target")) for r in rows)
    pass_count = sum(1 for r in rows if r.get("correctness") == "pass")
    updated = datetime.now().replace(microsecond=0).isoformat()
    cards = []
    fields = [
        "task_id",
        "priority_band",
        "assignment_points",
        "current_score",
        "gap_to_target",
        "total_cost",
        "correctness",
        "shape_class",
        "size_trend",
        "color_class",
        "candidate_id",
        "source_type",
        "onnx_template_candidate",
        "recoverability",
        "estimated_gain",
        "priority",
        "notes",
    ]
    for row in rows:
        status = "pass" if row.get("correctness") == "pass" else "fail" if row.get("correctness") == "fail" else "missing"
        search = " ".join(str(row.get(f, "")) for f in fields).lower()
        cards.append(
            "<section "
            f"class='card {status}' data-status='{status}' data-search='{html.escape(search)}' "
            f"data-task='{html.escape(str(row.get('task_id', '')))}' "
            f"data-score='{as_float(row.get('current_score')):.8f}' "
            f"data-gap='{as_float(row.get('gap_to_target')):.8f}' "
            f"data-cost='{as_float(row.get('total_cost')):.8f}' "
            f"data-priority='{as_float(row.get('priority')):.8f}'>"
            f"<div class='card-title'><span>{html.escape(str(row.get('task_id', '')))}</span>"
            f"<span>{as_float(row.get('current_score')):.4f}</span></div>"
            + "".join(f"<div><b>{html.escape(f)}</b>: {html.escape(str(row.get(f, '')))}</div>" for f in fields)
            + "</section>"
        )
    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Workplace {owner} NeuroGolf Dashboard</title>
<style>
*{{box-sizing:border-box}}body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f6f7f9;color:#111}}
header{{position:sticky;top:0;background:#fff;border-bottom:1px solid #d7dce2;padding:16px 20px;z-index:10}}
h1{{margin:0 0 12px;font-size:22px}}.summary{{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));gap:8px;margin-bottom:12px}}
.metric,.card{{background:#fff;border:1px solid #ddd;border-radius:6px;padding:10px}}.metric span{{display:block;color:#5b6470;font-size:12px}}.metric b{{font-size:18px}}
.toolbar{{display:grid;grid-template-columns:minmax(220px,1fr) 150px 170px 130px;gap:8px}}input,select,button{{border:1px solid #c8ced6;border-radius:6px;padding:8px 10px;font:inherit;background:#fff;color:#111}}
main{{padding:16px 20px}}.links{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px;font-size:13px}}.links a{{color:#1459a8;text-decoration:none}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px}}.card-title{{display:flex;justify-content:space-between;font-weight:700;margin-bottom:8px}}
.pass{{border-color:#2e7d32}}.fail{{border-color:#c62828;background:#fff4f4}}.missing{{border-color:#777;background:#f0f0f0}}.hidden{{display:none!important}}.card b{{display:inline-block;min-width:150px;color:#5b6470}}
@media(max-width:900px){{.summary{{grid-template-columns:repeat(2,1fr)}}.toolbar{{grid-template-columns:1fr}}.grid{{grid-template-columns:1fr}}}}
</style></head><body>
<header><h1>Workplace {html.escape(owner)} NeuroGolf Task Dashboard</h1>
<div class="summary">
<div class="metric"><span>assigned_tasks</span><b>{len(rows)}</b></div>
<div class="metric"><span>current_total_score</span><b>{total_score:.4f}</b></div>
<div class="metric"><span>gap_to_target</span><b>{total_gap:.4f}</b></div>
<div class="metric"><span>pass/tasks</span><b>{pass_count}/{len(rows)}</b></div>
<div class="metric"><span>visible/updated</span><b><span id="visible-count">{len(rows)}</span> / {updated}</b></div>
</div>
<div class="toolbar"><input id="q" placeholder="Search task, bucket, source, notes"><select id="status"><option value="">All statuses</option><option value="pass">pass</option><option value="fail">fail</option><option value="missing">missing</option></select><select id="sort"><option value="gap">Sort: gap desc</option><option value="priority">Sort: priority desc</option><option value="cost">Sort: cost desc</option><option value="score">Sort: score desc</option><option value="task">Sort: task id</option></select><button id="refresh" type="button">Refresh now</button></div>
</header><main>
<div class="links"><a href="task_progress_{owner}.csv">task_progress_{owner}.csv</a><a href="task_progress_{owner}.md">task_progress_{owner}.md</a><a href="../reports/onnx_visualization_sources.md">source notes</a><span>Auto-refreshes every 30 seconds when regenerated locally.</span></div>
<div class="grid">{''.join(cards)}</div>
</main>
<script>
const cards=[...document.querySelectorAll('.card')], q=document.querySelector('#q'), status=document.querySelector('#status'), sort=document.querySelector('#sort'), count=document.querySelector('#visible-count');
function val(card,key){{return Number(card.dataset[key]||0)}}function apply(){{const needle=q.value.trim().toLowerCase(), wanted=status.value;let visible=0;cards.forEach(card=>{{const show=(!needle||card.dataset.search.includes(needle))&&(!wanted||card.dataset.status===wanted);card.classList.toggle('hidden',!show);if(show)visible++}});const sorted=cards.slice().sort((a,b)=>sort.value==='task'?a.dataset.task.localeCompare(b.dataset.task):val(b,sort.value)-val(a,sort.value));const grid=document.querySelector('.grid');sorted.forEach(card=>grid.appendChild(card));count.textContent=visible}}q.addEventListener('input',apply);status.addEventListener('change',apply);sort.addEventListener('change',apply);document.querySelector('#refresh').addEventListener('click',()=>location.reload());apply();setTimeout(()=>location.reload(),30000);
</script></body></html>"""
    out.write_text(doc, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="C")
    parser.add_argument("--assignment-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    assignment_path = Path(args.assignment_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not TASK_TABLE.exists():
        raise SystemExit(f"task scoreboard missing: {TASK_TABLE}")

    task_rows = {r["task_id"]: r for r in read_csv(TASK_TABLE)}
    owner_assignments = [r for r in read_csv(assignment_path) if r.get("owner") == args.owner and r.get("assignment_type") == "primary"]
    merged: list[dict[str, Any]] = []
    for rec in owner_assignments:
        task_id = rec.get("task_id") or rec.get("task")
        if not task_id:
            continue
        row = dict(rec)
        row.update(task_rows.get(task_id, {}))
        row["task_id"] = task_id
        row["assignment_points"] = rec.get("points", "")
        row["priority_band"] = rec.get("priority_bucket") or rec.get("priority_band", "")
        row["shape_class"] = rec.get("shape_change") or rec.get("shape_class", "")
        row["size_trend"] = rec.get("size_change") or rec.get("size_trend", "")
        row["color_class"] = rec.get("palette_change") or rec.get("color_class", "")
        row["notes"] = row.get("notes") or rec.get("note", "")
        merged.append(row)
    merged.sort(key=lambda r: (as_float(r.get("gap_to_target")) * -1, r.get("task_id", "")))

    fields = [
        "task_id",
        "owner",
        "owner_track",
        "priority_band",
        "assignment_points",
        "current_score",
        "gap_to_target",
        "total_cost",
        "correctness",
        "shape_class",
        "size_trend",
        "color_class",
        "candidate_id",
        "source_type",
        "onnx_template_candidate",
        "recoverability",
        "estimated_gain",
        "priority",
        "notes",
    ]
    write_csv(out_dir / f"task_progress_{args.owner}.csv", merged, fields)
    report = [
        f"# Workplace {args.owner} Task Progress",
        "",
        f"updated_at: {datetime.now().replace(microsecond=0).isoformat()}",
        f"assigned_primary_tasks: {len(merged)}",
        f"current_total_score: {sum(as_float(r.get('current_score')) for r in merged):.6f}",
        f"total_gap_to_25_each: {sum(as_float(r.get('gap_to_target')) for r in merged):.6f}",
        "",
        "## Highest Gap Tasks",
        "",
        md_table(merged[:30], fields),
    ]
    (out_dir / f"task_progress_{args.owner}.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    render_owner_html(args.owner, merged, out_dir / "index.html")

    metadata = {
        "owner": args.owner,
        "task_count": len(merged),
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "source_task_scoreboard": str(TASK_TABLE),
        "source_assignment_csv": str(assignment_path),
    }
    (out_dir / "dashboard_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    shutil.copy2(TASK_TABLE, out_dir / "source_task_scoreboard_all_tasks.csv")
    print(f"exported={out_dir / 'index.html'}")
    print(f"tasks={len(merged)}")


if __name__ == "__main__":
    main()
