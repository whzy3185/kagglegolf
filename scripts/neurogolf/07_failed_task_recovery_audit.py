from __future__ import annotations

from _task_table import failed_task_recovery_audit


if __name__ == "__main__":
    rows = failed_task_recovery_audit()
    print(f"recovery_rows={len(rows)}")
