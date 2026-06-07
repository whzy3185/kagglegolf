from __future__ import annotations

import argparse
import shutil

from _bootstrap import ROOT
from neurogolf.submission import copy_onnx_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--exp-id", required=True)
    args = parser.parse_args()
    from neurogolf.paths import root

    base = root(args.base) if not args.base.startswith("/") else args.base
    target = root("submissions/candidates", args.exp_id, "onnx")
    copy_onnx_files(base, target)
    task_name = args.task if args.task.endswith(".onnx") else f"{args.task}.onnx"
    shutil.copy2(args.model, target / task_name)
    print(target)


if __name__ == "__main__":
    main()

