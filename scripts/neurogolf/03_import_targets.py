from __future__ import annotations

import argparse

from _task_table import import_targets


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    warnings = import_targets(args.input)
    print(f"warnings={len(warnings)}")
    for warning in warnings:
        print(f"warning: {warning}")
