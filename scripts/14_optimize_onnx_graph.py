from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from _bootstrap import ROOT
from neurogolf.onnx_rewrite import inline_model, inline_submission_dir, rewrite_model, rewrite_submission_dir


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="")
    parser.add_argument("--target", default="")
    parser.add_argument("--source-dir", default="")
    parser.add_argument("--target-dir", default="")
    parser.add_argument("--manifest", default="")
    parser.add_argument("--no-compress-uniform", action="store_true")
    parser.add_argument("--inline-functions", action="store_true")
    parser.add_argument("--replace-batch-compress", action="store_true")
    args = parser.parse_args()

    compress_uniform = not args.no_compress_uniform
    if args.source_dir:
        if not args.target_dir:
            raise SystemExit("--target-dir is required with --source-dir")
        source_dir = ROOT / args.source_dir
        target_dir = ROOT / args.target_dir
        if args.inline_functions:
            rows = inline_submission_dir(source_dir, target_dir)
        else:
            rows = rewrite_submission_dir(
                source_dir,
                target_dir,
                compress_uniform=compress_uniform,
                replace_batch_compress=args.replace_batch_compress,
            )
    elif args.source:
        if not args.target:
            raise SystemExit("--target is required with --source")
        if args.inline_functions:
            stats = inline_model(ROOT / args.source, ROOT / args.target)
        else:
            stats = rewrite_model(
                ROOT / args.source,
                ROOT / args.target,
                compress_uniform=compress_uniform,
                replace_batch_compress=args.replace_batch_compress,
            )
        rows = [stats.__dict__]
    else:
        raise SystemExit("provide --source/--target or --source-dir/--target-dir")

    manifest = {
        "source": args.source,
        "target": args.target,
        "source_dir": args.source_dir,
        "target_dir": args.target_dir,
        "compress_uniform": compress_uniform,
        "inline_functions": args.inline_functions,
        "replace_batch_compress": args.replace_batch_compress,
        "task_count": len(rows),
        "changed_count": sum(
            1
            for row in rows
            if row.get("changed") or row.get("status") in {"inlined", "rewritten"}
        ),
        "saved_parameters": sum(int(row.get("saved_parameters") or 0) for row in rows),
        "rows": rows,
    }
    if args.manifest:
        path = ROOT / args.manifest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        write_csv(path.with_suffix(".csv"), rows)
    print(json.dumps({k: v for k, v in manifest.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
