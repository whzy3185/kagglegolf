from __future__ import annotations

import argparse

from _bootstrap import ROOT
from neurogolf.evidence_gate import parse_direction_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--direction-id", default="")
    parser.add_argument("--exp-id", default="")
    args = parser.parse_args()

    directions = parse_direction_registry(ROOT / "research/DIRECTION_REGISTRY.md")
    if args.list:
        for direction_id in directions:
            print(direction_id)
        return
    if args.direction_id:
        direction = directions.get(args.direction_id)
        if not direction:
            raise SystemExit(f"Unknown direction_id: {args.direction_id}")
        print(direction["block"])
        return
    if args.exp_id:
        matches = [
            direction_id
            for direction_id, direction in directions.items()
            if args.exp_id in direction["target_exp_ids"]
        ]
        if not matches:
            raise SystemExit(f"No direction registered for exp_id: {args.exp_id}")
        print("\n".join(matches))
        return
    parser.error("Use --list, --direction-id, or --exp-id")


if __name__ == "__main__":
    main()
