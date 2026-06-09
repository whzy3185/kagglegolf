from __future__ import annotations

from _task_table import init_task_rows


if __name__ == "__main__":
    warnings = init_task_rows()
    for warning in warnings:
        print(f"warning: {warning}")
    print("task_table_initialized=400")
