from __future__ import annotations

from pathlib import Path


EVIDENCE_HEADER = """# Evidence Registry

All external sources used for candidates must be listed here before entering an experiment.

"""


def evidence_entry(
    source_id: str,
    source_type: str,
    title: str,
    author_or_team: str,
    url_or_identifier: str,
    date_accessed: str,
    claimed_score: str = "",
    idea_summary: str = "",
    implementation_hint: str = "",
    risk: str = "low",
    rule_status: str = "public_source",
    repro_status: str = "not_started",
    priority: str = "P1",
    assigned_exp_id: str = "",
    tasks_mentioned: str = "all",
) -> str:
    return f"""## {source_id}

source_id: {source_id}
source_type: {source_type}
title: {title}
author_or_team: {author_or_team}
url_or_identifier: {url_or_identifier}
date_accessed: {date_accessed}
claimed_score: {claimed_score}
tasks_mentioned: {tasks_mentioned}
idea_summary: {idea_summary}
implementation_hint: {implementation_hint}
risk: {risk}
rule_status: {rule_status}
repro_status: {repro_status}
priority: {priority}
assigned_exp_id: {assigned_exp_id}

"""


def append_if_missing(path: Path, source_id: str, entry: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = EVIDENCE_HEADER
    if f"source_id: {source_id}" not in text:
        text += entry
    path.write_text(text, encoding="utf-8")

