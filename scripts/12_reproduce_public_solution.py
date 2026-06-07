from __future__ import annotations

import argparse
import zipfile

from _bootstrap import ROOT
from neurogolf.kaggle_api import run_kaggle
from neurogolf.paths import root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="octaviograu/neurogolf-manual-rewrites-v205")
    parser.add_argument("--out-name", default="")
    args = parser.parse_args()
    name = args.out_name or args.dataset.split("/")[-1].replace("-", "_")
    out = root("data/external/public_bundles", name)
    out.mkdir(parents=True, exist_ok=True)
    result = run_kaggle(["datasets", "download", "-d", args.dataset, "-p", str(out), "--force"], cwd=ROOT, timeout=240)
    print(result.stdout)
    zips = list(out.glob("*.zip"))
    if zips:
        extracted = out / "extracted"
        extracted.mkdir(exist_ok=True)
        with zipfile.ZipFile(zips[0]) as zf:
            zf.extractall(extracted)
        print(extracted)
    else:
        print("No zip downloaded")


if __name__ == "__main__":
    main()

