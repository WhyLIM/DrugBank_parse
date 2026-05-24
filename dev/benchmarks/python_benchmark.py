from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Sequence

DEV_DIR = Path(__file__).resolve().parents[1]
PYTHON_PACKAGE_DIR = DEV_DIR / "python"
if str(PYTHON_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_PACKAGE_DIR))

from drugbank_parse import parse_drugbank_xml, write_drugbank_tables  # noqa: E402


def run_benchmark(
    input_path: str | Path,
    outdir: str | Path,
    metrics_path: str | Path,
    profile: str = "core",
) -> dict[str, Any]:
    xml_path = Path(input_path)
    output_dir = Path(outdir)
    metrics_file = Path(metrics_path)

    tracemalloc.start()
    start = time.perf_counter()
    result = parse_drugbank_xml(xml_path, profile=profile)
    written = write_drugbank_tables(result, output_dir)
    elapsed = time.perf_counter() - start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics: dict[str, Any] = {
        "implementation": "python",
        "input_path": str(xml_path),
        "profile": profile,
        "output_dir": str(output_dir),
        "elapsed_seconds": round(elapsed, 6),
        "peak_memory_mb": round(peak_bytes / (1024 * 1024), 3),
        "table_rows": {table: len(rows) for table, rows in result.tables.items()},
        "written_files": [path.name for path in written],
    }

    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_file.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark the Python DrugBank parser.")
    parser.add_argument("--input", required=True, help="Path to DrugBank XML.")
    parser.add_argument("--outdir", required=True, help="Directory for output CSV files.")
    parser.add_argument("--metrics", required=True, help="Path to write metrics JSON.")
    parser.add_argument("--profile", default="core", help="Parse profile. Default: core.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    metrics = run_benchmark(
        input_path=args.input,
        outdir=args.outdir,
        metrics_path=args.metrics,
        profile=args.profile,
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
