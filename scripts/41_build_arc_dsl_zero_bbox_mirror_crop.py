from __future__ import annotations

import argparse

from _bootstrap import ROOT
from neurogolf.onnx_build import build_zero_bbox_vertical_mirror_crop_network
from neurogolf.validation import validate_onnx_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--valid-width", type=int, default=16)
    parser.add_argument("--crop-size", type=int, default=3)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = ROOT / args.output
    build_zero_bbox_vertical_mirror_crop_network(
        output,
        valid_width=args.valid_width,
        crop_size=args.crop_size,
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
