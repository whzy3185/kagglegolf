from __future__ import annotations

from _task_table import correctness_audit


if __name__ == "__main__":
    rows = correctness_audit()
    bad = [r for r in rows if r["official_verify_status"] != "pass"]
    print(f"correctness_rows={len(rows)}")
    print(f"not_full_pass={len(bad)}")
