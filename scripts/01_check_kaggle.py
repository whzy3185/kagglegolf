from __future__ import annotations

import shutil

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root


def main() -> None:
    lines = ["# Kaggle CLI Check", ""]
    kaggle_path = shutil.which("kaggle")
    lines.append(f"kaggle_executable: {kaggle_path or 'missing'}")
    if not kaggle_path:
        lines.append("status: blocked")
        lines.append("fix: install kaggle CLI and place credentials outside the repo")
    else:
        for label, args in [
            ("version", ["--version"]),
            ("config", ["config", "view"]),
            ("competition", ["competitions", "list", "-s", "neurogolf"]),
            ("submissions", ["competitions", "submissions", "-c", "neurogolf-2026"]),
        ]:
            result = run_kaggle(args, cwd=ROOT, timeout=90)
            lines.append(f"\n## {label}\n")
            lines.append(result.stdout or "")
        lines.append("\nstatus: ok_if_competition_listed_and_no_auth_error")
    out = root("reports/kaggle_cli_check.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()

