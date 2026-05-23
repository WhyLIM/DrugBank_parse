# DrugBank Parse Dev Rewrite

This directory contains the new package-first DrugBank XML parsers.

## Python Core Parser

Install test dependencies from `dev/python`:

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

## Core Output Tables

- `drugs.csv`
- `targets.csv`
- `drug_target.csv`
- `drug_indication.csv`
- `target_drug_indication.csv`
