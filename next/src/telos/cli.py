"""The `telos` command."""

import argparse
import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path

from telos import __version__

DEFAULT_DATA_DIR = Path.home() / ".telos"
"""Provisional: R1.5 discovers the data directory per platform."""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="telos", description=__doc__)
    parser.add_argument("--version", action="version", version=f"telos {__version__}")
    commands = parser.add_subparsers(dest="command")
    serve = commands.add_parser("serve", help="run Telos until stopped (SIGTERM, Ctrl+C)")
    serve.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args(argv)
    if args.command == "serve":
        from telos.host.serve import serve as run

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        return asyncio.run(run(args.data_dir))
    parser.print_help()
    return 0
