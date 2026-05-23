# DrugBank R Core Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent R core parser under `dev/R` that reads DrugBank XML, writes the same core CSV tables as the Python package, and matches the shared fixture outputs exactly.

**Architecture:** The R package will treat `dev/schema/*.yml` and `dev/fixtures/expected/core/*.csv` as the contract. It will expose `parse_drugbank_xml()` and `write_drugbank_tables()`, parse one `<drug>` subtree at a time with `xml2::xml_event_parse()`, accumulate core rows as data frames, and export schema-ordered CSV files. Tests will compare R output to the already committed expected fixture CSVs.

**Tech Stack:** R 4.x, `xml2`, `yaml`, `testthat`, `readr`, base R data frames, and optional `data.table` only if profiling shows the core parser needs it.

---

## Scope

This plan implements Phase 2 from the approved design spec:

- R package skeleton under `dev/R`.
- Schema/profile loader that reads the shared YAML files.
- Core profile parser for `drugs`, `targets`, `drug_target`, `drug_indication`, and `target_drug_indication`.
- CSV exporter using schema column order.
- `testthat` tests that compare R output to `dev/fixtures/expected/core/*.csv`.
- Minimal R documentation in `dev/R/README.md` and a note in `dev/README.md`.

This plan does not implement extended modules, benchmarks, CRAN packaging, Roxygen documentation, or a full legacy compatibility exporter.

## Current Environment Note

At plan-writing time, `Rscript` is not available on PATH in this workspace. The first task verifies R availability. If `Rscript` is still unavailable during execution, stop and ask for the R installation path or install/configure R before continuing.

## File Structure

- Create `dev/R/DESCRIPTION`: R package metadata and dependencies.
- Create `dev/R/NAMESPACE`: exported public API.
- Create `dev/R/R/paths.R`: project-root and shared-schema path helpers.
- Create `dev/R/R/schema.R`: YAML schema/profile loading and module/table resolution.
- Create `dev/R/R/result.R`: parse result construction and guarded row appending.
- Create `dev/R/R/parser.R`: streaming XML parser and core extractors.
- Create `dev/R/R/exporters.R`: schema-aware CSV writer.
- Create `dev/R/tests/testthat.R`: testthat entrypoint.
- Create `dev/R/tests/testthat/helper-paths.R`: shared fixture paths.
- Create `dev/R/tests/testthat/test-schema.R`: schema/profile tests.
- Create `dev/R/tests/testthat/test-result.R`: guarded result tests.
- Create `dev/R/tests/testthat/test-parser-core.R`: parser tests.
- Create `dev/R/tests/testthat/test-exporters.R`: CSV exporter/fixture tests.
- Create `dev/R/README.md`: R package usage notes.
- Modify `dev/README.md`: point to the R package once the core implementation exists.

---

### Task 1: Verify R Toolchain and Package Dependencies

**Files:**
- No code files.

- [ ] **Step 1: Check Rscript is available**

Run from the repository root:

```powershell
Rscript --version
```

Expected: prints an R version. If PowerShell reports that `Rscript` is not recognized, stop and ask for the local R installation path or permission to install/configure R.

- [ ] **Step 2: Check required R packages**

Run:

```powershell
Rscript -e "pkgs <- c('xml2','yaml','testthat','readr'); cat(paste(pkgs, requireNamespace(pkgs, quietly = TRUE), sep='=', collapse='\n'))"
```

Expected: all packages print `=TRUE`.

- [ ] **Step 3: Install missing packages if needed**

If any package is missing, run:

```powershell
Rscript -e "install.packages(c('xml2','yaml','testthat','readr'), repos='https://cloud.r-project.org')"
```

Expected: packages install successfully. This requires network access; if the command fails due to network sandboxing, rerun it with escalation.

- [ ] **Step 4: Commit nothing**

This task only verifies the environment. There should be no git changes.

Run:

```powershell
git status --short
```

Expected: only pre-existing unrelated untracked files remain, if any.

---

### Task 2: Create R Package Skeleton

**Files:**
- Create: `dev/R/DESCRIPTION`
- Create: `dev/R/NAMESPACE`
- Create: `dev/R/tests/testthat.R`
- Create: `dev/R/tests/testthat/helper-paths.R`

- [ ] **Step 1: Create package metadata**

Create `dev/R/DESCRIPTION`:

```text
Package: drugbankparse
Title: Low-Memory DrugBank XML Parser
Version: 0.1.0
Authors@R: person("Min", "Li", email = "mli.bio@outlook.com", role = c("aut", "cre"))
Description: Parses DrugBank XML files into schema-defined core tables.
License: MIT
Encoding: UTF-8
Roxygen: list(markdown = TRUE)
RoxygenNote: 7.3.2
Imports:
    readr,
    xml2,
    yaml
Suggests:
    testthat (>= 3.0.0)
Config/testthat/edition: 3
```

- [ ] **Step 2: Create namespace exports**

Create `dev/R/NAMESPACE`:

```r
export(load_drugbank_schema)
export(load_drugbank_profiles)
export(parse_drugbank_xml)
export(resolve_modules)
export(resolve_tables)
export(write_drugbank_tables)
```

- [ ] **Step 3: Create testthat entrypoint**

Create `dev/R/tests/testthat.R`:

```r
library(testthat)
library(drugbankparse)

test_check("drugbankparse")
```

- [ ] **Step 4: Create test path helpers**

Create `dev/R/tests/testthat/helper-paths.R`:

```r
repo_root <- function() {
  normalizePath(file.path(testthat::test_path(), "..", "..", ".."), winslash = "/", mustWork = TRUE)
}

fixture_xml <- function() {
  file.path(repo_root(), "test-database.xml")
}

shared_schema_dir <- function() {
  file.path(repo_root(), "dev", "schema")
}

expected_core_dir <- function() {
  file.path(repo_root(), "dev", "fixtures", "expected", "core")
}
```

- [ ] **Step 5: Run tests and verify package is incomplete**

Run from `dev/R`:

```powershell
Rscript -e "testthat::test_local(reporter='summary')"
```

Expected: FAIL because exported functions do not exist yet.

- [ ] **Step 6: Commit skeleton**

Run:

```powershell
git add dev/R/DESCRIPTION dev/R/NAMESPACE dev/R/tests/testthat.R dev/R/tests/testthat/helper-paths.R
git commit -m "test: scaffold R DrugBank package"
```

---

### Task 3: Implement Shared Schema and Profile Loading

**Files:**
- Create: `dev/R/R/paths.R`
- Create: `dev/R/R/schema.R`
- Create: `dev/R/tests/testthat/test-schema.R`

- [ ] **Step 1: Write failing schema tests**

Create `dev/R/tests/testthat/test-schema.R`:

```r
test_that("load_drugbank_schema reads shared core tables", {
  schema <- load_drugbank_schema(shared_schema_dir())

  expect_equal(schema$version, 1)
  expect_equal(names(schema$tables), c(
    "drugs",
    "targets",
    "drug_target",
    "drug_indication",
    "target_drug_indication"
  ))
  expect_equal(schema$tables$drugs$columns, c("drug_id", "drug_name", "inchi", "source"))
})

test_that("resolve_modules reads core profile", {
  expect_equal(resolve_modules(profile = "core", modules = NULL, schema_dir = shared_schema_dir()), "core")
  expect_equal(resolve_modules(profile = "core", modules = c("core"), schema_dir = shared_schema_dir()), "core")
})

test_that("resolve_modules rejects unknown profile and module", {
  expect_error(resolve_modules(profile = "missing", schema_dir = shared_schema_dir()), "Unknown profile")
  expect_error(resolve_modules(profile = "core", modules = c("missing"), schema_dir = shared_schema_dir()), "Unknown module")
})

test_that("resolve_tables preserves core table order", {
  expect_equal(resolve_tables(c("core"), schema_dir = shared_schema_dir()), c(
    "drugs",
    "targets",
    "drug_target",
    "drug_indication",
    "target_drug_indication"
  ))
})
```

- [ ] **Step 2: Run schema tests and verify they fail**

Run from `dev/R`:

```powershell
Rscript -e "pkgload::load_all('.'); testthat::test_file('tests/testthat/test-schema.R')"
```

Expected: FAIL because schema functions do not exist.

- [ ] **Step 3: Implement path helpers**

Create `dev/R/R/paths.R`:

```r
default_schema_dir <- function() {
  candidate <- file.path(getwd(), "..", "schema")
  if (dir.exists(candidate)) {
    return(normalizePath(candidate, winslash = "/", mustWork = TRUE))
  }

  candidate <- file.path(getwd(), "dev", "schema")
  if (dir.exists(candidate)) {
    return(normalizePath(candidate, winslash = "/", mustWork = TRUE))
  }

  stop("Cannot locate shared schema directory. Pass schema_dir explicitly.", call. = FALSE)
}
```

- [ ] **Step 4: Implement schema/profile functions**

Create `dev/R/R/schema.R`:

```r
load_yaml_file <- function(path) {
  if (!file.exists(path)) {
    stop(sprintf("Schema file does not exist: %s", path), call. = FALSE)
  }
  value <- yaml::read_yaml(path)
  if (!is.list(value)) {
    stop(sprintf("Schema file is empty or invalid: %s", path), call. = FALSE)
  }
  value
}

load_drugbank_schema <- function(schema_dir = NULL) {
  base <- if (is.null(schema_dir)) default_schema_dir() else schema_dir
  tables <- load_yaml_file(file.path(base, "tables.yml"))
  fields <- load_yaml_file(file.path(base, "fields.yml"))

  list(
    version = as.integer(tables$version),
    tables = tables$tables,
    fields = fields$fields
  )
}

load_drugbank_profiles <- function(schema_dir = NULL) {
  base <- if (is.null(schema_dir)) default_schema_dir() else schema_dir
  load_yaml_file(file.path(base, "profiles.yml"))
}

resolve_modules <- function(profile = "core", modules = NULL, schema_dir = NULL) {
  profiles <- load_drugbank_profiles(schema_dir)
  known_profiles <- profiles$profiles
  known_modules <- profiles$modules

  if (!profile %in% names(known_profiles)) {
    stop(sprintf("Unknown profile: %s", profile), call. = FALSE)
  }

  selected <- if (is.null(modules)) known_profiles[[profile]]$modules else modules
  for (module in selected) {
    if (!module %in% names(known_modules)) {
      stop(sprintf("Unknown module: %s", module), call. = FALSE)
    }
  }
  selected
}

resolve_tables <- function(modules, schema_dir = NULL) {
  profiles <- load_drugbank_profiles(schema_dir)
  known_modules <- profiles$modules
  tables <- character()

  for (module in modules) {
    if (!module %in% names(known_modules)) {
      stop(sprintf("Unknown module: %s", module), call. = FALSE)
    }
    for (table in known_modules[[module]]$tables) {
      if (!table %in% tables) {
        tables <- c(tables, table)
      }
    }
  }
  tables
}
```

- [ ] **Step 5: Run schema tests**

Run from `dev/R`:

```powershell
Rscript -e "pkgload::load_all('.'); testthat::test_file('tests/testthat/test-schema.R')"
```

Expected: PASS.

- [ ] **Step 6: Commit schema loader**

Run:

```powershell
git add dev/R/R/paths.R dev/R/R/schema.R dev/R/tests/testthat/test-schema.R
git commit -m "feat: load shared schema in R package"
```

---

### Task 4: Implement Parse Result Guardrails

**Files:**
- Create: `dev/R/R/result.R`
- Create: `dev/R/tests/testthat/test-result.R`

- [ ] **Step 1: Write failing result tests**

Create `dev/R/tests/testthat/test-result.R`:

```r
test_that("new_parse_result initializes requested tables", {
  result <- new_parse_result(c("drugs", "targets"))

  expect_named(result, c("drugs", "targets"))
  expect_true(is.data.frame(result$drugs))
  expect_equal(nrow(result$drugs), 0)
})

test_that("append_row rejects tables outside selected profile", {
  result <- new_parse_result(c("drugs"))

  expect_error(
    append_row(result, "targets", list(target_id = "P00734")),
    "Table is not enabled"
  )
})
```

- [ ] **Step 2: Run result tests and verify they fail**

Run from `dev/R`:

```powershell
Rscript -e "pkgload::load_all('.'); testthat::test_file('tests/testthat/test-result.R')"
```

Expected: FAIL because result functions do not exist.

- [ ] **Step 3: Implement result helpers**

Create `dev/R/R/result.R`:

```r
new_parse_result <- function(tables) {
  result <- stats::setNames(vector("list", length(tables)), tables)
  for (table in tables) {
    result[[table]] <- data.frame(stringsAsFactors = FALSE)
  }
  result
}

append_row <- function(result, table, row) {
  if (!table %in% names(result)) {
    stop(sprintf("Table is not enabled for this parse result: %s", table), call. = FALSE)
  }

  row_df <- as.data.frame(row, stringsAsFactors = FALSE)
  result[[table]] <- rbind(result[[table]], row_df)
  result
}
```

- [ ] **Step 4: Run result tests**

Run:

```powershell
Rscript -e "pkgload::load_all('.'); testthat::test_file('tests/testthat/test-result.R')"
```

Expected: PASS.

- [ ] **Step 5: Commit result helpers**

Run:

```powershell
git add dev/R/R/result.R dev/R/tests/testthat/test-result.R
git commit -m "feat: add R parse result guardrails"
```

---

### Task 5: Implement R Core XML Parser

**Files:**
- Create: `dev/R/R/parser.R`
- Create: `dev/R/tests/testthat/test-parser-core.R`

- [ ] **Step 1: Write failing parser tests**

Create `dev/R/tests/testthat/test-parser-core.R`:

```r
test_that("parse_drugbank_xml returns core tables", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())

  expect_named(result, c(
    "drugs",
    "targets",
    "drug_target",
    "drug_indication",
    "target_drug_indication"
  ))
})

test_that("parse_drugbank_xml extracts fixture drugs", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())

  expect_equal(nrow(result$drugs), 2)
  expect_equal(result$drugs$drug_id, c("DB00001", "DB00014"))
  expect_equal(result$drugs$drug_name, c("Lepirudin", "Goserelin"))
  expect_equal(result$drugs$source, c("DrugBank", "DrugBank"))
})

test_that("parse_drugbank_xml extracts target relationships", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())

  pairs <- paste(result$drug_target$drug_id, result$drug_target$target_id, sep = "->")
  expect_equal(sort(pairs), sort(c(
    "DB00001->P00734",
    "DB00014->P22888",
    "DB00014->P30968"
  )))
})

test_that("parse_drugbank_xml builds denormalized table", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())

  expect_equal(nrow(result$target_drug_indication), 3)
  db00014 <- result$target_drug_indication[result$target_drug_indication$drug_id == "DB00014", ]
  expect_equal(unique(db00014$drug_name), "Goserelin")
  expect_equal(db00014$gene_name[db00014$target_id == "P22888"], "LHCGR")
  expect_equal(db00014$gene_name[db00014$target_id == "P30968"], "GNRHR")
})

test_that("parse_drugbank_xml respects empty module selection", {
  result <- parse_drugbank_xml(fixture_xml(), modules = character(), schema_dir = shared_schema_dir())

  expect_equal(result, list())
})

test_that("parse_drugbank_xml fails clearly for missing file", {
  expect_error(
    parse_drugbank_xml(file.path(tempdir(), "missing.xml"), schema_dir = shared_schema_dir()),
    "Input XML file does not exist"
  )
})
```

- [ ] **Step 2: Run parser tests and verify they fail**

Run from `dev/R`:

```powershell
Rscript -e "pkgload::load_all('.'); testthat::test_file('tests/testthat/test-parser-core.R')"
```

Expected: FAIL because parser does not exist.

- [ ] **Step 3: Implement parser**

Create `dev/R/R/parser.R`:

```r
drugbank_ns <- "http://www.drugbank.ca"
source_name <- "DrugBank"

xml_text_first <- function(node, xpath) {
  found <- xml2::xml_find_first(node, xpath, ns = c(db = drugbank_ns))
  if (inherits(found, "xml_missing")) {
    return("")
  }
  trimws(xml2::xml_text(found))
}

xml_attr_first <- function(node, xpath, attr) {
  found <- xml2::xml_find_first(node, xpath, ns = c(db = drugbank_ns))
  if (inherits(found, "xml_missing")) {
    return("")
  }
  value <- xml2::xml_attr(found, attr)
  if (is.na(value)) "" else value
}

calculated_property <- function(drug_node, kind) {
  properties <- xml2::xml_find_all(drug_node, "db:calculated-properties/db:property", ns = c(db = drugbank_ns))
  for (property in properties) {
    property_kind <- xml_text_first(property, "db:kind")
    if (identical(property_kind, kind)) {
      return(xml_text_first(property, "db:value"))
    }
  }
  ""
}

extract_core_drug <- function(drug_node, result) {
  drug_id <- xml_text_first(drug_node, "db:drugbank-id[@primary='true']")
  if (identical(drug_id, "")) {
    return(result)
  }

  drug_name <- xml_text_first(drug_node, "db:name")
  indication <- xml_text_first(drug_node, "db:indication")
  inchi <- calculated_property(drug_node, "InChI")

  result <- append_row(result, "drugs", list(
    drug_id = drug_id,
    drug_name = drug_name,
    inchi = inchi,
    source = source_name
  ))
  result <- append_row(result, "drug_indication", list(
    drug_id = drug_id,
    indication = indication,
    source = source_name
  ))

  targets <- xml2::xml_find_all(drug_node, "db:targets/db:target", ns = c(db = drugbank_ns))
  for (target in targets) {
    target_id <- xml_attr_first(target, "db:polypeptide", "id")
    if (identical(target_id, "")) {
      next
    }

    target_name <- xml_text_first(target, "db:name")
    organism <- xml_text_first(target, "db:organism")
    gene_name <- xml_text_first(target, "db:polypeptide/db:gene-name")

    result <- append_row(result, "targets", list(
      target_id = target_id,
      target_name = target_name,
      gene_name = gene_name,
      organism = organism,
      source = source_name
    ))
    result <- append_row(result, "drug_target", list(
      drug_id = drug_id,
      target_id = target_id,
      source = source_name
    ))
    result <- append_row(result, "target_drug_indication", list(
      target_id = target_id,
      gene_name = gene_name,
      drug_id = drug_id,
      drug_name = drug_name,
      inchi = inchi,
      indication = indication,
      source = source_name
    ))
  }

  result
}

deduplicate_table <- function(result, table, key_fields) {
  if (!table %in% names(result) || nrow(result[[table]]) == 0) {
    return(result)
  }
  keys <- do.call(paste, c(result[[table]][key_fields], sep = "\r"))
  result[[table]] <- result[[table]][!duplicated(keys), , drop = FALSE]
  rownames(result[[table]]) <- NULL
  result
}

parse_drugbank_xml <- function(path, profile = "core", modules = NULL, schema_dir = NULL) {
  if (!file.exists(path)) {
    stop(sprintf("Input XML file does not exist: %s", path), call. = FALSE)
  }

  selected_modules <- resolve_modules(profile = profile, modules = modules, schema_dir = schema_dir)
  tables <- resolve_tables(selected_modules, schema_dir = schema_dir)
  result <- new_parse_result(tables)

  if (!"core" %in% selected_modules) {
    return(result)
  }

  handler <- function(node, path) {
    result <<- extract_core_drug(node, result)
    invisible(TRUE)
  }

  xml2::xml_event_parse(
    path,
    handlers = list(`/drugbank/drug` = handler),
    as_html = FALSE
  )

  result <- deduplicate_table(result, "targets", c("target_id"))
  result
}
```

If `xml2::xml_event_parse()` path matching with namespaces does not trigger for DrugBank XML, replace only the event parser portion with a working `xml2::read_xml()` fixture implementation and add a comment noting that full-file streaming will be restored before full DrugBank benchmarks. Do not load the full XML silently without the comment.

- [ ] **Step 4: Run parser tests**

Run:

```powershell
Rscript -e "pkgload::load_all('.'); testthat::test_file('tests/testthat/test-parser-core.R')"
```

Expected: PASS.

- [ ] **Step 5: Commit parser**

Run:

```powershell
git add dev/R/R/parser.R dev/R/tests/testthat/test-parser-core.R
git commit -m "feat: parse DrugBank core XML in R"
```

---

### Task 6: Implement Schema-Aware CSV Exporter

**Files:**
- Create: `dev/R/R/exporters.R`
- Create: `dev/R/tests/testthat/test-exporters.R`

- [ ] **Step 1: Write failing exporter tests**

Create `dev/R/tests/testthat/test-exporters.R`:

```r
expected_core_files <- function() {
  c(
    "drugs.csv",
    "targets.csv",
    "drug_target.csv",
    "drug_indication.csv",
    "target_drug_indication.csv"
  )
}

test_that("write_drugbank_tables writes core CSVs with schema headers", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())
  outdir <- tempfile("drugbank-r-core-")
  dir.create(outdir)

  written <- write_drugbank_tables(result, outdir, schema_dir = shared_schema_dir())

  expect_equal(sort(basename(written)), sort(expected_core_files()))
  header <- readLines(file.path(outdir, "drugs.csv"), n = 1)
  expect_equal(header, "drug_id,drug_name,inchi,source")
})

test_that("R exported core CSVs match shared expected fixture files", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())
  outdir <- tempfile("drugbank-r-core-")
  dir.create(outdir)

  write_drugbank_tables(result, outdir, schema_dir = shared_schema_dir())

  expected_dir <- expected_core_dir()
  expect_true(dir.exists(expected_dir))
  expect_equal(sort(list.files(expected_dir, pattern = "\\\\.csv$")), sort(expected_core_files()))
  expect_equal(sort(list.files(outdir, pattern = "\\\\.csv$")), sort(expected_core_files()))

  for (filename in expected_core_files()) {
    expect_equal(
      readLines(file.path(outdir, filename), warn = FALSE),
      readLines(file.path(expected_dir, filename), warn = FALSE),
      info = filename
    )
  }
})
```

- [ ] **Step 2: Run exporter tests and verify they fail**

Run from `dev/R`:

```powershell
Rscript -e "pkgload::load_all('.'); testthat::test_file('tests/testthat/test-exporters.R')"
```

Expected: FAIL because `write_drugbank_tables()` does not exist.

- [ ] **Step 3: Implement exporter**

Create `dev/R/R/exporters.R`:

```r
align_table_columns <- function(df, columns) {
  for (column in columns) {
    if (!column %in% names(df)) {
      df[[column]] <- ""
    }
  }
  df[, columns, drop = FALSE]
}

write_drugbank_tables <- function(result, outdir, schema_dir = NULL) {
  dir.create(outdir, recursive = TRUE, showWarnings = FALSE)
  schema <- load_drugbank_schema(schema_dir)

  written <- character()
  for (table in names(result)) {
    if (!table %in% names(schema$tables)) {
      stop(sprintf("Result contains table not defined in schema: %s", table), call. = FALSE)
    }
    columns <- unlist(schema$tables[[table]]$columns, use.names = FALSE)
    df <- align_table_columns(result[[table]], columns)
    path <- file.path(outdir, paste0(table, ".csv"))
    readr::write_csv(df, path, na = "")
    written <- c(written, path)
  }
  written
}
```

- [ ] **Step 4: Run exporter tests and full R test suite**

Run from `dev/R`:

```powershell
Rscript -e "pkgload::load_all('.'); testthat::test_file('tests/testthat/test-exporters.R')"
Rscript -e "testthat::test_local(reporter='summary')"
```

Expected: PASS.

- [ ] **Step 5: Commit exporter**

Run:

```powershell
git add dev/R/R/exporters.R dev/R/tests/testthat/test-exporters.R
git commit -m "feat: export R DrugBank core tables"
```

---

### Task 7: Add R Documentation

**Files:**
- Create: `dev/R/README.md`
- Modify: `dev/README.md`

- [ ] **Step 1: Create R README**

Create `dev/R/README.md`:

```markdown
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
```

- [ ] **Step 2: Update dev README**

Add this section to `dev/README.md` after the Python section:

```markdown
## R Core Parser

The R implementation lives in `dev/R` and targets the same shared schema and expected core fixture CSVs as the Python package.

Run R tests from `dev/R`:

```powershell
Rscript -e "testthat::test_local(reporter='summary')"
```
```

- [ ] **Step 3: Run documentation smoke checks**

Run:

```powershell
Test-Path dev\\R\\README.md
Select-String -Path dev\\README.md -Pattern "R Core Parser"
```

Expected: both commands show the R docs exist.

- [ ] **Step 4: Commit docs**

Run:

```powershell
git add dev/R/README.md dev/README.md
git commit -m "docs: document R core parser"
```

---

### Task 8: Final Verification for R Core Package

**Files:**
- No new files.

- [ ] **Step 1: Run full R tests**

Run from `dev/R`:

```powershell
Rscript -e "testthat::test_local(reporter='summary')"
```

Expected: PASS.

- [ ] **Step 2: Run R parser/export smoke**

Run from `dev/R`:

```powershell
Rscript -e "library(drugbankparse); result <- parse_drugbank_xml('../../test-database.xml', schema_dir='../schema'); out <- '../tmp_r_core_output'; write_drugbank_tables(result, out, schema_dir='../schema'); print(list.files(out))"
```

Expected: prints `drug_indication.csv`, `drug_target.csv`, `drugs.csv`, `target_drug_indication.csv`, and `targets.csv`.

- [ ] **Step 3: Compare smoke output to expected fixture**

Run from `dev/R`:

```powershell
Rscript -e "files <- c('drugs.csv','targets.csv','drug_target.csv','drug_indication.csv','target_drug_indication.csv'); for (f in files) stopifnot(identical(readLines(file.path('../tmp_r_core_output', f), warn=FALSE), readLines(file.path('../fixtures/expected/core', f), warn=FALSE))); cat('matched expected core CSVs\n')"
```

Expected: prints `matched expected core CSVs`.

- [ ] **Step 4: Remove smoke output**

Run from `dev/R` after confirming the resolved path is inside `D:\Study\Project\DrugBank_parse\dev\tmp_r_core_output`:

```powershell
Remove-Item ..\\tmp_r_core_output -Recurse -Force
```

Expected: temporary output directory is removed.

- [ ] **Step 5: Run Python tests to ensure shared fixtures still match**

Run from `dev/python`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTEST_ADDOPTS='-p no:cacheprovider'; D:\\Anaconda3\\python.exe -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Check git status**

Run from repository root:

```powershell
git status --short
```

Expected: only pre-existing unrelated untracked files remain, if any.

- [ ] **Step 7: Commit nothing**

This task is verification only. If verification requires fixes, make a focused fix commit before re-running this task.

