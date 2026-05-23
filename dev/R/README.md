# drugbankparse R Package

This package is the R implementation of the DrugBank core parser. It reads the shared schema in `../schema` and writes the same core CSV tables as the Python implementation.

## Run Tests

From `dev/R`:

```powershell
Rscript -e "testthat::test_local(reporter='summary')"
```

## Use The Parser

```r
library(drugbankparse)

result <- parse_drugbank_xml("../../test-database.xml", schema_dir = "../schema")
write_drugbank_tables(result, "../tmp_r_core_output", schema_dir = "../schema")
```

## Core Output Tables

- `drugs.csv`
- `targets.csv`
- `drug_target.csv`
- `drug_indication.csv`
- `target_drug_indication.csv`
