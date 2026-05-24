# DrugBank Parse Dev Rewrite

This directory contains the new package-first DrugBank XML parsers.

## Python Core Parser

Run these commands from `dev/python`.

Install test dependencies:

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

## R Core Parser

The R implementation lives in `dev/R` and targets the same shared schema and expected core fixture CSVs as the Python package.

Run R tests from `dev/R`:

```powershell
Rscript -e "testthat::test_local(reporter='summary')"
```

Parse the bundled fixture from `dev/R`:

```r
library(drugbankparse)

result <- parse_drugbank_xml("../../test-database.xml", schema_dir = "../schema")
write_drugbank_tables(result, "tmp_r_core_output", schema_dir = "../schema")
```

## Core Output Tables

- `drugs.csv`
- `targets.csv`
- `drug_target.csv`
- `drug_indication.csv`
- `target_drug_indication.csv`

## Benchmarks

Benchmark scripts live in `dev/benchmarks`. Start with the bundled fixture before running a full DrugBank XML file.

From `dev/benchmarks`:

```powershell
D:\Anaconda3\python.exe python_benchmark.py --input ..\..\test-database.xml --outdir tmp_python_core --metrics tmp_python_core_metrics.json
D:\R\R-4.5.3\bin\Rscript.exe r_benchmark.R --input ..\..\test-database.xml --outdir tmp_r_core --metrics tmp_r_core_metrics.json
```
