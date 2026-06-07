from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from io import StringIO

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root


def _parse_rows(text: str) -> list[dict]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines or "No submissions found" in text:
        return []
    csv_result = run_kaggle(["competitions", "submissions", "-c", "neurogolf-2026", "-v"], cwd=ROOT, timeout=90)
    csv_text = csv_result.stdout or ""
    if "," in csv_text and "ref" in csv_text.splitlines()[0].lower():
        return [dict(row) for row in csv.DictReader(StringIO(csv_text)) if any(row.values())]

    rows = []
    for line in lines:
        if line.startswith("-") or line.strip().startswith("ref "):
            continue
        m = re.match(
            r"^\s*(?P<ref>\d+)\s+(?P<fileName>\S+)\s+(?P<date>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+(?P<rest>.+?)\s+(?P<status>SubmissionStatus\.\S+)\s*(?P<publicScore>[0-9.]+)?\s*(?P<privateScore>[0-9.]+)?\s*$",
            line,
        )
        if not m:
            continue
        row = m.groupdict()
        row["description"] = row.pop("rest").strip()
        rows.append(row)
    return rows


def _score(row: dict) -> float | None:
    value = row.get("publicScore") or row.get("public_score") or row.get("score")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _exp_id(row: dict) -> str:
    desc = row.get("description") or row.get("Description") or ""
    return desc.split("|", 1)[0].strip()


def _load_json(path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_best_manifest(best_row: dict | None, best_score: float | None) -> dict:
    if not best_row:
        return {}
    exp_id = _exp_id(best_row)
    submitted_path = root("submissions", "submitted", exp_id, "manifest.json")
    current_path = root("submissions", "best", "current_best_manifest.json")
    base = _load_json(submitted_path) or _load_json(current_path)
    manifest = {
        **base,
        "exp_id": exp_id,
        "score": best_score,
        "submission_id": best_row.get("ref"),
        "status": str(best_row.get("status", "")).replace("SubmissionStatus.", "").lower() or "complete",
    }

    best_dir = root("submissions", "best", exp_id)
    best_dir.mkdir(parents=True, exist_ok=True)
    best_manifest_text = json.dumps(manifest, indent=2)
    best_dir.joinpath("manifest.json").write_text(best_manifest_text, encoding="utf-8")
    current_path.write_text(best_manifest_text, encoding="utf-8")

    score_lines = [
        f"# {exp_id}",
        "",
        f"submission id: {best_row.get('ref')}",
        f"public score: {best_score}",
        f"status: {best_row.get('status')}",
        f"source ids: {', '.join(manifest.get('source_ids', []))}",
        f"local validation: {manifest.get('local_validation', '')}",
        f"examples checked: {manifest.get('examples_checked', '')}",
        f"examples failed: {manifest.get('examples_failed', '')}",
        f"notebook output ONNX matched: {manifest.get('notebook_output_match', '')}",
        f"package sha256: {manifest.get('package_sha256', '')}",
        "",
    ]
    score_text = "\n".join(score_lines)
    best_dir.joinpath("score.md").write_text(score_text, encoding="utf-8")
    root("submissions", "best", "current_best.md").write_text(
        "\n".join(
            [
                "# Current Best",
                "",
                f"exp_id: {exp_id}",
                f"submission id: {best_row.get('ref')}",
                f"public score: {best_score}",
                f"status: {str(best_row.get('status', '')).replace('SubmissionStatus.', '').lower()}",
                f"source ids: {', '.join(manifest.get('source_ids', []))}",
                f"local validation: {manifest.get('local_validation', '')}",
                f"examples checked: {manifest.get('examples_checked', '')}",
                f"examples failed: {manifest.get('examples_failed', '')}",
                f"notebook output ONNX matched: {manifest.get('notebook_output_match', '')}",
                f"package sha256: {manifest.get('package_sha256', '')}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest


def _write_reports(rows: list[dict], raw_text: str) -> None:
    scored = [(row, _score(row)) for row in rows]
    scored = [(row, score) for row, score in scored if score is not None]
    best_row, best_score = (max(scored, key=lambda item: item[1]) if scored else (None, None))
    best_manifest = _write_best_manifest(best_row, best_score)
    payload = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "competition": "neurogolf-2026",
        "selected_submissions": "unavailable via CLI",
        "fallback_top2_public_score": [
            {
                "ref": row.get("ref"),
                "exp_id": _exp_id(row),
                "publicScore": score,
                "status": row.get("status"),
                "date": row.get("date"),
            }
            for row, score in sorted(scored, key=lambda item: item[1], reverse=True)[:2]
        ],
        "best_public": {
            "ref": best_row.get("ref") if best_row else "",
            "exp_id": _exp_id(best_row) if best_row else "",
            "publicScore": best_score,
            "status": best_row.get("status") if best_row else "",
            "date": best_row.get("date") if best_row else "",
        },
        "rows": rows,
        "raw": raw_text,
    }
    root("data/manifests/kaggle_submission_history.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    table_rows = []
    for row in rows:
        table_rows.append(
            "| {ref} | {exp_id} | {date} | {status} | {public} |".format(
                ref=row.get("ref", ""),
                exp_id=_exp_id(row),
                date=row.get("date", ""),
                status=row.get("status", ""),
                public=row.get("publicScore") or "",
            )
        )
    report = "\n".join(
        [
            "# Kaggle Submission History",
            "",
            f"captured_at: {payload['captured_at']}",
            "selected submissions: unavailable via CLI",
            f"current best public: {payload['best_public'].get('publicScore')}",
            f"current best exp_id: {payload['best_public'].get('exp_id')}",
            f"current best submission id: {payload['best_public'].get('ref')}",
            "",
            "| ref | exp_id | date | status | public_score |",
            "| --- | --- | --- | --- | --- |",
            *table_rows,
            "",
        ]
    )
    root("reports/KAGGLE_SUBMISSION_HISTORY.md").write_text(report, encoding="utf-8")
    scorecard = "\n".join(
        [
            "# Scorecard",
            "",
            f"Current best public score: {payload['best_public'].get('publicScore')}",
            f"Current best exp_id: {payload['best_public'].get('exp_id')}",
            f"Current best submission id: {payload['best_public'].get('ref')}",
            "",
            "Selected submissions: unavailable via CLI; fallback is top 2 by public score.",
            "",
            "| ref | exp_id | status | public_score |",
            "| --- | --- | --- | --- |",
            *[
                f"| {row.get('ref', '')} | {_exp_id(row)} | {row.get('status', '')} | {row.get('publicScore') or ''} |"
                for row in rows
            ],
            "",
        ]
    )
    root("reports/SCORECARD.md").write_text(scorecard, encoding="utf-8")

    if best_row:
        exp_id = _exp_id(best_row)
        local_validation = best_manifest.get("local_validation", "unknown")
        examples_checked = best_manifest.get("examples_checked", "")
        examples_failed = best_manifest.get("examples_failed", "")
        root("reports/CURRENT_STATE.md").write_text(
            "\n".join(
                [
                    "# Current State",
                    "",
                    f"Current best LB: {best_score}",
                    "Current best local score: not computed",
                    f"Current best local validation: {local_validation}, {examples_checked} checked, {examples_failed} failed",
                    f"Current best manifest path: submissions/best/{exp_id}/manifest.json",
                    f"Current best candidate artifact path: submissions/candidates/{exp_id}/submission.zip",
                    "Current candidate in queue:",
                    f"Current submitted candidate: {exp_id} / submission {best_row.get('ref')} / status {best_row.get('status')}",
                    "Current running Kaggle Notebook: https://www.kaggle.com/code/muelsyse111/neurogolf-submit-current (version 3 submitted via output file)",
                    "Next candidate: GOLF_20260607_002_public_6029_diff",
                    "Known blockers:",
                    f"Last updated: {payload['captured_at']}",
                    "",
                ]
            ),
            encoding="utf-8",
        )


def main() -> None:
    result = run_kaggle(["competitions", "submissions", "-c", "neurogolf-2026"], cwd=ROOT, timeout=90)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = root("reports", f"submissions_raw_{ts}.txt")
    raw_text = result.stdout or ""
    out.write_text(raw_text, encoding="utf-8")
    root("reports/SUBMISSION_HISTORY_LATEST.txt").write_text(raw_text, encoding="utf-8")
    _write_reports(_parse_rows(raw_text), raw_text)
    print(out)


if __name__ == "__main__":
    main()
