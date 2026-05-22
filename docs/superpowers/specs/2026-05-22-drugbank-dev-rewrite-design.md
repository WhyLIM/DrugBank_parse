# DrugBank Dev Rewrite Design

## Context

The existing project parses DrugBank XML files to extract drug, target, indication, InChI, and mapping tables. The current codebase contains several historical implementations:

- `v1/`: early Python SAX parser and R post-processing scripts.
- `v2/`: more readable Python SAX parser and R post-processing scripts.
- `vR/`: R event-parser implementation.
- `dev/`: unfinished experiments using `lxml` and `xml2`.

The rewrite will make `dev/` the new development line. The goal is to build readable, low-memory, fast parsers that extract richer DrugBank data while preserving simple workflows for core mapping tables.

## Decisions

The new `dev/` implementation will use a lightweight package-first structure for both Python and R.

The Python and R versions will share a schema and test expectations, but each implementation will parse XML independently. This keeps both versions genuinely usable while preventing output drift.

Parsing will be profile-based:

- `core`: default, fast profile for the original project use case.
- `extended`: richer profile for additional DrugBank entities.
- `custom modules`: user-selected feature groups for balancing speed, memory, and detail.

## Goals

- Keep code easy to read and maintain.
- Minimize memory use on full DrugBank XML files.
- Keep parsing fast enough for repeated local use.
- Extract richer data than the legacy scripts.
- Produce consistent output tables from Python and R.
- Support package APIs first, with command-line entry points as convenience wrappers.
- Avoid hard-coded local paths, XML versions, and output locations.

## Non-Goals

- The first version will not be a full DrugBank mirror.
- The first version will not implement a database backend.
- The first version will not depend on Python from R or R from Python.
- The first version will not preserve every historical output quirk if a cleaner schema is available.

## Proposed Directory Structure

```text
dev/
  schema/
    tables.yml
    fields.yml
    profiles.yml
  fixtures/
    test-database.xml
    expected/
      core/
      extended/
  python/
    pyproject.toml
    drugbank_parse/
      __init__.py
      parser.py
      models.py
      profiles.py
      exporters.py
      cli.py
    tests/
  R/
    DESCRIPTION
    R/
      parser.R
      profiles.R
      exporters.R
      schema.R
    tests/testthat/
```

## Output Profiles

### Core Profile

The core profile replaces and cleans up the legacy project outputs.

Expected tables:

- `drugs`: one row per primary DrugBank drug.
- `targets`: one row per target polypeptide identifier observed in drug target records.
- `drug_target`: one row per drug-target relationship.
- `drug_indication`: one row per drug and indication text.
- `target_drug_indication`: denormalized table for downstream analysis.

Core fields include:

- `drug_id`
- `drug_name`
- `inchi`
- `indication`
- `target_id`
- `target_name`
- `gene_name`
- `organism`
- `source`

### Extended Profile

The extended profile adds richer DrugBank entities.

Expected additional tables:

- `drug_interactions`
- `drug_external_ids`
- `calculated_properties`
- `target_external_ids`
- `target_references`
- `drug_references`
- `go_classifiers`
- `pfams`
- `sequences`
- `snp_effects`

Extended modules should be selectable so users can request only the costly or relevant parts they need.

## Schema

`dev/schema/` is the contract between Python and R. It defines table names, columns, required fields, profile membership, and stable column ordering.

The schema should use simple YAML files because they are readable and easy for both Python and R to load. If YAML dependencies become undesirable, each package may include a generated schema object, but the YAML files remain the canonical source.

Column names should use snake_case consistently. Legacy names such as `DrugID`, `UniprotAC`, and `GeneName` can be supported only through compatibility exporters if needed.

## Python Design

The Python package should live in `dev/python/drugbank_parse`.

Primary API:

```python
from drugbank_parse import parse_drugbank_xml, write_drugbank_tables

result = parse_drugbank_xml(
    "drugbank_5-1-12.xml",
    profile="core",
    modules=None,
)
write_drugbank_tables(result, "output")
```

Implementation approach:

- Use `lxml.etree.iterparse` with end events on `drug` nodes.
- Parse one `<drug>` subtree at a time.
- Clear processed XML nodes immediately to control memory.
- Keep extraction functions small and field-focused.
- Store parsed tables as lightweight lists of dictionaries during the first implementation.
- Convert to CSV only at export time.

The parser should be structured around module extractors. Core extractors always run in the `core` profile. Extended extractors run only when selected by profile or module list.

## R Design

The R package should live in `dev/R`.

Primary API:

```r
library(drugbankparse)

result <- parse_drugbank_xml(
  "drugbank_5-1-12.xml",
  profile = "core",
  modules = NULL
)
write_drugbank_tables(result, "output")
```

Implementation approach:

- Prefer event-based parsing to avoid loading the full XML document.
- Use `XML::xmlEventParse` for streaming if it remains the most reliable option.
- Keep parser state explicit and documented.
- Use `data.table` for efficient table assembly and CSV export.
- Match Python output schemas exactly.

Some extended modules may be harder to express with event parsing. For those modules, the R implementation may use small, isolated helper functions as long as it does not load the full DrugBank XML into memory.

## Data Flow

1. User selects input XML, profile, optional modules, and output directory.
2. Parser resolves the effective module set from `profiles.yml`.
3. Parser streams through the XML drug by drug.
4. Enabled extractors collect rows into named table buffers.
5. Exporter validates each table against the schema.
6. Exporter writes stable CSV files with consistent column order.

## Error Handling

The parsers should fail clearly when:

- The input XML file does not exist.
- The selected profile is unknown.
- A selected module is unknown.
- A required schema file is missing or invalid.
- Required output columns cannot be produced.

Missing optional XML fields should produce empty values, not parser failures.

Malformed XML should surface the underlying parser error with the input path included in the message.

## Testing

Shared fixtures will live under `dev/fixtures/`.

The existing `test-database.xml` should be copied into `dev/fixtures/test-database.xml` or referenced by tests through a stable fixture path.

Python tests should use `pytest`. R tests should use `testthat`.

Both implementations should test:

- Core profile parses the fixture successfully.
- Output tables match expected column names and ordering.
- Primary DrugBank IDs are extracted correctly.
- Drug-target relationships are extracted correctly.
- Gene names are associated with target IDs correctly.
- Unknown profiles and modules fail with clear errors.
- Exported CSV files match expected fixture outputs for the core profile.

Extended profile tests can start with presence and shape checks, then grow into exact expected output tests as modules stabilize.

## Performance Strategy

Performance work should be measured against the full DrugBank XML file when available locally.

Initial benchmark metrics:

- Runtime for `core`.
- Runtime for `extended`.
- Peak memory for `core`.
- Peak memory for `extended`.
- Number of output rows per table.

The first optimization priority is memory stability. Runtime optimizations should not make the code much harder to read unless benchmarks show a meaningful gain.

## Implementation Phases

### Phase 1: Python Core Package

Build the schema, Python package skeleton, core parser, core exporters, CLI wrapper, and fixture tests.

### Phase 2: R Core Package

Build the R package skeleton, schema loader, core parser, exporters, and fixture tests matching Python output.

### Phase 3: Extended Modules

Add extended extractors in small groups:

1. Drug interactions and drug external identifiers.
2. Calculated properties and references.
3. Target external identifiers, GO, Pfam, and sequences.
4. SNP effects.

Each group should include schema updates and tests in both Python and R.

### Phase 4: Benchmarks and Documentation

Add benchmark scripts, update README quick-start examples, and document profile/module choices.

## Open Compatibility Policy

The new canonical output uses snake_case columns and normalized tables.

If legacy compatibility is needed, add an explicit compatibility exporter rather than shaping the new schema around historical quirks. For example, a compatibility exporter may write files named `XML_dbid_dname.csv`, `XML_tgid_dbid.csv`, and `DrugBank_TDI.csv`.

## Approval

This design reflects the approved direction:

- Lightweight package-first rewrite.
- Configurable parsing profiles and modules.
- Shared schema and tests for Python/R.
- Independent Python and R implementations.
