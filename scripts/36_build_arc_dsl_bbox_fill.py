from __future__ import annotations

import argparse

from _bootstrap import ROOT
from neurogolf.onnx_build import build_bbox_delta_fill_network
from neurogolf.validation import validate_onnx_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--source-color", type=int, required=True)
    parser.add_argument("--fill-color", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = ROOT / args.output
    build_bbox_delta_fill_network(
        output,
        source_color=args.source_color,
        fill_color=args.fill_color,
    )
    result = validate_onnx_file(
        output,
        ROOT / "data/raw/neurogolf-2026",
        smoke_examples_per_split=10_000,
    )
    print(f"path={output}")
    print(f"ok={result.ok}")
    print(f"examples_checked={result.examples_checked}")
    print(f"examples_failed={result.examples_failed}")
    if not result.ok:
        print("\n".join(result.structural_errors))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
