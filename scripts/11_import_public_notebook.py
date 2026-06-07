from __future__ import annotations

import argparse

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="jsrdcht/6029-09-lb-neurogolf-all-task-onnx-solution")
    parser.add_argument("--name", default="")
    args = parser.parse_args()
    name = args.name or args.ref.replace("/", "_").replace("-", "_")
    out = root("external/public_notebooks", name)
    out.mkdir(parents=True, exist_ok=True)
    result = run_kaggle(["kernels", "pull", args.ref, "-p", str(out), "-m"], cwd=ROOT, timeout=180)
    print(result.stdout)
    print(out)


if __name__ == "__main__":
    main()

