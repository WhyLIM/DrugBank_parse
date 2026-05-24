# DrugBank_parse

Parse downloaded DrugBank XML files into drug, target, indication, and drug-target mapping tables.

This repository now contains two generations of code:

- `dev/`: the current package-first rewrite, with shared schema definitions and matching Python/R core parsers.
- `v1`, `v2`, `vR`: legacy scripts kept for reference and compatibility experiments.

The rewrite is the recommended path for new work.

## Current Status

The `dev/` implementation currently supports the core DrugBank output contract:

- Python package: `dev/python`
- R package: `dev/R`
- Shared schema: `dev/schema`
- Expected fixture CSVs: `dev/fixtures/expected/core`

Both Python and R implementations parse the bundled `test-database.xml` fixture and export the same core CSV files.

## Core Output Tables

- `drugs.csv`
- `targets.csv`
- `drug_target.csv`
- `drug_indication.csv`
- `target_drug_indication.csv`

## Python Quick Start

Run these commands from `dev/python`.

Install the package with test dependencies:

```powershell
python -m pip install -e ".[test]"
```

Run tests:

```powershell
python -m pytest -q
```

Parse the bundled fixture:

```powershell
python -m drugbank_parse.cli --input ..\..\test-database.xml --profile core --outdir ..\tmp_core_output
```

Use the package API:

```python
from drugbank_parse import parse_drugbank_xml, write_drugbank_tables

result = parse_drugbank_xml("drugbank_5-1-12.xml", profile="core")
write_drugbank_tables(result, "output")
```

## R Quick Start

Run these commands from `dev/R`.

Run tests:

```powershell
Rscript -e "testthat::test_local(reporter='summary')"
```

Use the package API after installing or loading the package:

```r
library(drugbankparse)

result <- parse_drugbank_xml("../../test-database.xml", schema_dir = "../schema")
write_drugbank_tables(result, "tmp_r_core_output", schema_dir = "../schema")
```

## Directory Guide

- `dev/README.md`: detailed notes for the current rewrite.
- `dev/python`: Python core parser package and tests.
- `dev/R`: R core parser package and tests.
- `dev/schema`: shared YAML table/profile definitions.
- `dev/fixtures`: small fixture data and expected core CSV outputs.
- `v1`: early Python parser with faster parsing but harder-to-read code.
- `v2`: more readable Python parser with slower file processing.
- `vR`: older R scripts with low memory usage but much slower runtime.
- `test-database.xml`: small DrugBank XML fixture for tests.

## DrugBank XML Input

Download full DrugBank XML releases from:

https://go.drugbank.com/releases/latest

The legacy scripts were tested against DrugBank release `v5.1.12`. The current rewrite uses `test-database.xml` and shared fixture CSVs as its regression contract while the full-file parser is being expanded.

## Notes

The rewrite is intentionally schema-driven so Python and R exports stay aligned. Add new fields or tables by updating `dev/schema` first, then extending the Python/R parsers and expected fixtures together.
