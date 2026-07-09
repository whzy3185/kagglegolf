from __future__ import annotations

import argparse
import http.server
import socketserver
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "neurogolf_task_table"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if not (DATA_DIR / "task_scoreboard.html").exists():
        raise SystemExit(f"dashboard missing: {DATA_DIR / 'task_scoreboard.html'}")

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(DATA_DIR))
    with socketserver.TCPServer((args.host, args.port), handler) as server:
        url = f"http://{args.host}:{args.port}/task_scoreboard.html"
        print(f"serving={url}")
        print(f"root={DATA_DIR}")
        server.serve_forever()


if __name__ == "__main__":
    main()
