from __future__ import annotations

import csv
from pathlib import Path

from .models import ParseResult
from .schema import load_schema


def write_drugbank_tables(
    result: ParseResult,
    outdir: str | Path,
) -> list[Path]:
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)
    schema = load_schema()

    written: list[Path] = []
    for table_name, rows in result.tables.items():
        if table_name not in schema.tables:
            raise ValueError(f"Result contains table not defined in schema: {table_name}")

        table_schema = schema.tables[table_name]
        path = output_dir / f"{table_name}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=table_schema.columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in table_schema.columns})
        written.append(path)

    return written
