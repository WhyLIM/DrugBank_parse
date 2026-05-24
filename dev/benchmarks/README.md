# DrugBank Parser Benchmarks

These scripts run fixture or full-XML smoke benchmarks for the current `dev/` parsers. They write parser output CSV files plus a small metrics JSON file with elapsed time and table row counts.

Use fixture runs first. Full DrugBank XML runs can take much longer; the R parser is streaming but still slower than the Python implementation because it currently accumulates rows in base R data frames.

## Python

From `dev/benchmarks`:

```powershell
D:\Anaconda3\python.exe python_benchmark.py --input ..\..\test-database.xml --outdir tmp_python_core --metrics tmp_python_core_metrics.json
```

For a full local XML file:

```powershell
D:\Anaconda3\python.exe python_benchmark.py --input ..\..\drugbank_5-1-12.xml --outdir tmp_python_full --metrics tmp_python_full_metrics.json
```

## R

From `dev/benchmarks`:

```powershell
D:\R\R-4.5.3\bin\Rscript.exe r_benchmark.R --input ..\..\test-database.xml --outdir tmp_r_core --metrics tmp_r_core_metrics.json
```

For a full local XML file:

```powershell
D:\R\R-4.5.3\bin\Rscript.exe r_benchmark.R --input ..\..\drugbank_5-1-12.xml --outdir tmp_r_full --metrics tmp_r_full_metrics.json
```

## Metrics

Each metrics JSON includes:

- `implementation`
- `input_path`
- `profile`
- `output_dir`
- `elapsed_seconds`
- `table_rows`
- `written_files`

## Local Full XML Baseline

On `drugbank_5-1-12.xml` in this workspace:

- Python core parser: about `59.13` seconds, with `27.844 MB` Python tracemalloc peak memory.
- R core parser: about `240.59` seconds after list-accumulator optimization.

Both implementations produced matching CSV content for the five core tables.
