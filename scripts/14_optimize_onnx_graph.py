from __future__ import annotations

import argparse

from _bootstrap import ROOT
from neurogolf.onnx_rewrite import copy_as_rewrite


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    copy_as_rewrite(ROOT / args.source, ROOT / args.target)
    print(args.target)


if __name__ == "__main__":
    main()

