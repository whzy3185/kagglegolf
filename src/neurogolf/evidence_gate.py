from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path

import yaml


EVIDENCE_FIELDS = [
    "direction_id",
    "leaderboard_source_id",
    "paper_source_id",
    "open_repo_source_id",
    "historical_competition_source_id",
]

BASIS_TO_FIELD = {
    "leaderboard_basis": "leaderboard_source_id",
    "paper_basis": "paper_source_id",
    "open_repo_basis": "open_repo_source_id",
    "historical_competition_basis": "historical_competition_source_id",
}

FIELD_TO_GROUP = {
    "leaderboard_source_id": "leaderboard",
    "paper_source_id": "paper",
    "open_repo_source_id": "open_repo",
    "historical_competition_source_id": "historical_competition",
}


def load_config(root: Path) -> dict:
    return yaml.safe_load((root / "configs/evidence_gate.yaml").read_text(encoding="utf-8"))


def parse_evidence_registry(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"(?m)^source_id:\s*(\S+)\s*$", text))
    sources: dict[str, dict] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end]
        source_type = re.search(r"(?m)^source_type:\s*(\S+)\s*$", block)
        sources[match.group(1)] = {
            "source_id": match.group(1),
            "source_type": source_type.group(1) if source_type else "",
        }
    return sources


def parse_direction_registry(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    headers = list(re.finditer(r"(?m)^##\s+(DIR_\S+)\s*$", text))
    directions: dict[str, dict] = {}
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[header.start() : end]
        direction_id = header.group(1)
        targets_match = re.search(
            r"(?ms)^target_exp_ids:\s*\n(?P<body>(?:\s{2}-[^\n]*\n?)*)",
            block,
        )
        targets = (
            re.findall(r"(?m)^\s{2}-\s*(\S+)\s*$", targets_match.group("body"))
            if targets_match
            else []
        )
        bases: dict[str, dict] = {}
        for basis in BASIS_TO_FIELD:
            basis_match = re.search(
                rf"(?ms)^{basis}:\s*\n\s{{2}}source_id:\s*(\S+)\s*\n\s{{2}}reason:\s*(.+?)(?=\n\n|\Z)",
                block,
            )
            bases[basis] = {
                "source_id": basis_match.group(1) if basis_match else "",
                "reason": basis_match.group(2).strip() if basis_match else "",
            }
        status_match = re.search(r"(?m)^status:\s*(\S+)\s*$", block)
        directions[direction_id] = {
            "direction_id": direction_id,
            "status": status_match.group(1) if status_match else "",
            "target_exp_ids": targets,
            "bases": bases,
            "block": block.strip(),
        }
    return directions


def read_experiments(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def is_exempt(row: dict, config: dict) -> tuple[bool, str]:
    lane = row.get("lane", "")
    exempt_lanes = set(config.get("exempt_lanes", []))
    if lane not in exempt_lanes:
        return False, ""
    if config.get("exempt_requires_parent_exp_id", False) and not row.get("parent_exp_id"):
        return False, "exempt_lane_missing_parent_exp_id"
    return True, f"exempt_lane:{lane}"


def validate_row(
    row: dict,
    *,
    config: dict,
    sources: dict[str, dict],
    directions: dict[str, dict],
) -> dict:
    exp_id = row.get("exp_id", "")
    exempt, exempt_reason = is_exempt(row, config)
    result = {
        "exp_id": exp_id,
        "direction_id": row.get("direction_id", ""),
        "status": "exempt" if exempt else "pass",
        "reasons": [exempt_reason] if exempt_reason else [],
    }
    if exempt:
        return result

    reasons: list[str] = []
    for field, required in config.get("required_for_every_exp", {}).items():
        if required and not row.get(field):
            reasons.append(f"missing:{field}")

    direction_id = row.get("direction_id", "")
    direction = directions.get(direction_id)
    if direction_id and not direction:
        reasons.append(f"unknown_direction_id:{direction_id}")
    elif direction:
        if exp_id not in direction.get("target_exp_ids", []):
            reasons.append(f"exp_not_registered_in_direction:{direction_id}")

    allowed_groups = config.get("source_type_groups", {})
    for field, group in FIELD_TO_GROUP.items():
        source_id = row.get(field, "")
        if not source_id:
            continue
        source = sources.get(source_id)
        if not source:
            reasons.append(f"unknown_source_id:{field}:{source_id}")
            continue
        allowed_types = set(allowed_groups.get(group, []))
        if source.get("source_type") not in allowed_types:
            reasons.append(
                f"invalid_source_type:{field}:{source_id}:{source.get('source_type')}"
            )

    result["status"] = "fail" if reasons else "pass"
    result["reasons"] = reasons
    return result


def validate_experiments(
    root: Path,
    *,
    exp_id: str = "",
    direction_id: str = "",
) -> dict:
    config = load_config(root)
    sources = parse_evidence_registry(root / "research/EVIDENCE_REGISTRY.md")
    directions = parse_direction_registry(root / "research/DIRECTION_REGISTRY.md")
    rows = read_experiments(root / "experiments/experiments.csv")
    if exp_id:
        rows = [row for row in rows if row.get("exp_id") == exp_id]
    if direction_id:
        rows = [row for row in rows if row.get("direction_id") == direction_id]

    if (exp_id or direction_id) and not rows:
        selector = f"exp_id:{exp_id}" if exp_id else f"direction_id:{direction_id}"
        results = [
            {
                "exp_id": exp_id or "",
                "direction_id": direction_id or "",
                "status": "fail",
                "reasons": [f"selector_not_found:{selector}"],
            }
        ]
    else:
        results = [
            validate_row(row, config=config, sources=sources, directions=directions)
            for row in rows
        ]
    checked_at = datetime.now().isoformat(timespec="seconds")
    payload = {
        "checked_at": checked_at,
        "strict_mode": bool(config.get("strict_mode", False)),
        "filters": {"exp_id": exp_id, "direction_id": direction_id},
        "total_experiments": len(results),
        "pass_count": sum(item["status"] == "pass" for item in results),
        "fail_count": sum(item["status"] == "fail" for item in results),
        "exempt_count": sum(item["status"] == "exempt" for item in results),
        "failed_exp_ids": [
            item["exp_id"] for item in results if item["status"] == "fail"
        ],
        "results": results,
    }
    return payload


def write_gate_outputs(root: Path, payload: dict) -> None:
    manifest_path = root / "data/manifests/evidence_gate_status.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    failed = [item for item in payload["results"] if item["status"] == "fail"]
    passed = [item for item in payload["results"] if item["status"] == "pass"]
    exempt = [item for item in payload["results"] if item["status"] == "exempt"]
    lines = [
        "# Evidence Gate Status",
        "",
        f"checked_at: {payload['checked_at']}",
        f"strict_mode: {str(payload['strict_mode']).lower()}",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| total_experiments | {payload['total_experiments']} |",
        f"| pass | {payload['pass_count']} |",
        f"| fail | {payload['fail_count']} |",
        f"| exempt | {payload['exempt_count']} |",
        "",
        "## Required Evidence",
        "",
        "Every non-exempt experiment must include:",
        "",
        "- leaderboard_source_id",
        "- paper_source_id",
        "- open_repo_source_id",
        "- historical_competition_source_id",
        "",
        "## Failed Experiments",
        "",
    ]
    if failed:
        for item in failed:
            lines.append(f"- {item['exp_id']}: {', '.join(item['reasons'])}")
    else:
        lines.append("None.")
    lines.extend(["", "## Passed Experiments", ""])
    lines.extend(f"- {item['exp_id']}" for item in passed)
    lines.extend(["", "## Exempt Experiments", ""])
    if exempt:
        lines.extend(
            f"- {item['exp_id']}: {', '.join(item['reasons'])}" for item in exempt
        )
    else:
        lines.append("None.")
    lines.append("")
    (root / "reports/EVIDENCE_GATE_STATUS.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def update_candidate_manifest(root: Path, exp_id: str, result: dict) -> None:
    path = root / "submissions/candidates" / exp_id / "manifest.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["evidence_gate_status"] = result["status"]
    payload["evidence_gate_checked_at"] = datetime.now().isoformat(timespec="seconds")
    payload["evidence_gate_notes"] = "; ".join(result.get("reasons", []))
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def update_submission_queue(root: Path, results: list[dict]) -> None:
    path = root / "experiments/submission_queue.csv"
    if not path.exists() or not path.stat().st_size:
        return
    by_exp = {item["exp_id"]: item for item in results if item.get("exp_id")}
    if not by_exp:
        return
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if "evidence_gate_status" not in fields:
        fields.append("evidence_gate_status")
    for row in rows:
        result = by_exp.get(row.get("exp_id", ""))
        if result:
            row["evidence_gate_status"] = result["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fields} for row in rows)
