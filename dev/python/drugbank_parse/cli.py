from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .exporters import write_drugbank_tables
from .parser import parse_drugbank_xml


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse DrugBank XML into CSV tables.")
    parser.add_argument("--input", required=True, help="Path to DrugBank XML file.")
    parser.add_argument("--outdir", required=True, help="Directory for output CSV files.")
    parser.add_argument("--profile", default="core", help="Parse profile. Default: core.")
    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        help="Module to enable. May be passed multiple times.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = parse_drugbank_xml(
        Path(args.input),
        profile=args.profile,
        modules=args.modules,
    )
    written = write_drugbank_tables(result, Path(args.outdir))
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
