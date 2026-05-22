# DrugBank Python Core Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first shippable `dev/` rewrite slice: shared schema files, fixture expectations, and a lightweight Python package that parses the DrugBank core profile and writes stable CSV tables.

**Architecture:** The shared schema under `dev/schema/` defines table names, column ordering, profiles, and modules. The Python package under `dev/python/drugbank_parse/` loads that schema, streams DrugBank XML one `<drug>` node at a time with `lxml.etree.iterparse`, accumulates normalized core rows, and exports CSV files through a schema-aware exporter.

**Tech Stack:** Python 3.9+, `lxml`, `PyYAML`, `pytest`, standard-library `csv`, `argparse`, `pathlib`, and `dataclasses`.

---

## Scope

This plan implements Phase 1 from the approved design spec:

- Shared core schema.
- Python package skeleton.
- Core profile parser.
- Core CSV exporter.
- Python CLI wrapper.
- Fixture-based tests using the existing `test-database.xml`.

This plan deliberately does not implement the R package, extended profile modules, benchmarks, or legacy compatibility exporters. Those become follow-up plans once the Python core contract is stable.

## File Structure

- Create `dev/schema/tables.yml`: canonical table definitions, columns, and required fields.
- Create `dev/schema/profiles.yml`: profile-to-module mapping.
- Create `dev/schema/fields.yml`: field descriptions for documentation and validation messages.
- Create `dev/fixtures/expected/core/drugs.csv`: expected core fixture output.
- Create `dev/fixtures/expected/core/targets.csv`: expected core fixture output.
- Create `dev/fixtures/expected/core/drug_target.csv`: expected core fixture output.
- Create `dev/fixtures/expected/core/drug_indication.csv`: expected core fixture output.
- Create `dev/fixtures/expected/core/target_drug_indication.csv`: expected core fixture output.
- Create `dev/python/pyproject.toml`: package metadata and test dependencies.
- Create `dev/python/drugbank_parse/__init__.py`: public package API.
- Create `dev/python/drugbank_parse/models.py`: result and schema dataclasses.
- Create `dev/python/drugbank_parse/schema.py`: schema loading and validation.
- Create `dev/python/drugbank_parse/profiles.py`: profile/module resolution.
- Create `dev/python/drugbank_parse/parser.py`: streaming XML parser and core extractors.
- Create `dev/python/drugbank_parse/exporters.py`: CSV writer.
- Create `dev/python/drugbank_parse/cli.py`: command-line entry point.
- Create `dev/python/tests/conftest.py`: fixture paths and import setup.
- Create `dev/python/tests/test_schema.py`: schema loader tests.
- Create `dev/python/tests/test_profiles.py`: profile resolution tests.
- Create `dev/python/tests/test_parser_core.py`: core parser tests.
- Create `dev/python/tests/test_exporters.py`: CSV exporter tests.
- Create `dev/python/tests/test_cli.py`: CLI smoke tests.

## Assumptions

- The existing root fixture `test-database.xml` remains available and is committed.
- Core parser tests may reference `../../test-database.xml` instead of copying the file, avoiding fixture duplication.
- The fixture contains the first DrugBank drug, so exact expected row counts should be confirmed during implementation by inspecting parser output once tests are being written.
- If the local Python environment lacks dependencies, install them in the active environment or create a `.venv`; do not vendor dependencies into the repository.

---

### Task 1: Create Shared Core Schema

**Files:**
- Create: `dev/schema/tables.yml`
- Create: `dev/schema/profiles.yml`
- Create: `dev/schema/fields.yml`
- Test: `dev/python/tests/test_schema.py`

- [ ] **Step 1: Create the schema files**

Create `dev/schema/tables.yml` with this content:

```yaml
version: 1
tables:
  drugs:
    description: One row per primary DrugBank drug.
    columns:
      - drug_id
      - drug_name
      - inchi
      - source
    required:
      - drug_id
      - drug_name
      - source
  targets:
    description: One row per target polypeptide identifier.
    columns:
      - target_id
      - target_name
      - gene_name
      - organism
      - source
    required:
      - target_id
      - source
  drug_target:
    description: One row per drug-target relationship.
    columns:
      - drug_id
      - target_id
      - source
    required:
      - drug_id
      - target_id
      - source
  drug_indication:
    description: One row per drug and indication text.
    columns:
      - drug_id
      - indication
      - source
    required:
      - drug_id
      - source
  target_drug_indication:
    description: Denormalized target-drug-indication table.
    columns:
      - target_id
      - gene_name
      - drug_id
      - drug_name
      - inchi
      - indication
      - source
    required:
      - target_id
      - drug_id
      - source
```

Create `dev/schema/profiles.yml` with this content:

```yaml
version: 1
profiles:
  core:
    modules:
      - core
modules:
  core:
    tables:
      - drugs
      - targets
      - drug_target
      - drug_indication
      - target_drug_indication
```

Create `dev/schema/fields.yml` with this content:

```yaml
version: 1
fields:
  drug_id: Primary DrugBank identifier.
  drug_name: Drug display name.
  inchi: InChI calculated property when available.
  indication: Drug indication text.
  target_id: Target polypeptide identifier, usually a UniProt accession.
  target_name: DrugBank target name.
  gene_name: Gene symbol associated with a target polypeptide.
  organism: Target organism.
  source: Data source label.
```

- [ ] **Step 2: Create the first failing schema test**

Create `dev/python/tests/test_schema.py`:

```python
from drugbank_parse.schema import load_schema


def test_load_schema_returns_core_tables():
    schema = load_schema()

    assert schema.version == 1
    assert list(schema.tables) == [
        "drugs",
        "targets",
        "drug_target",
        "drug_indication",
        "target_drug_indication",
    ]
    assert schema.tables["drugs"].columns == [
        "drug_id",
        "drug_name",
        "inchi",
        "source",
    ]
```

- [ ] **Step 3: Run the schema test and verify it fails**

Run:

```powershell
cd dev\python
python -m pytest tests\test_schema.py -q
```

Expected: FAIL because the Python package and `load_schema` do not exist yet.

- [ ] **Step 4: Commit the schema files and failing test**

Run:

```powershell
git add dev\schema dev\python\tests\test_schema.py
git commit -m "test: define DrugBank core schema contract"
```

---

### Task 2: Create Python Package Skeleton and Schema Loader

**Files:**
- Create: `dev/python/pyproject.toml`
- Create: `dev/python/drugbank_parse/__init__.py`
- Create: `dev/python/drugbank_parse/models.py`
- Create: `dev/python/drugbank_parse/schema.py`
- Modify: `dev/python/tests/test_schema.py`

- [ ] **Step 1: Create package metadata**

Create `dev/python/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "drugbank-parse"
version = "0.1.0"
description = "Low-memory DrugBank XML parser."
readme = "../../README.md"
requires-python = ">=3.9"
dependencies = [
  "lxml>=4.9",
  "PyYAML>=6.0",
]

[project.optional-dependencies]
test = [
  "pytest>=8.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create dataclasses**

Create `dev/python/drugbank_parse/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TableSchema:
    name: str
    description: str
    columns: list[str]
    required: list[str]


@dataclass(frozen=True)
class DrugBankSchema:
    version: int
    tables: dict[str, TableSchema]
    fields: dict[str, str]


@dataclass
class ParseResult:
    tables: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def add_row(self, table: str, row: dict[str, str]) -> None:
        self.tables.setdefault(table, []).append(row)

    def rows(self, table: str) -> list[dict[str, str]]:
        return self.tables.get(table, [])
```

- [ ] **Step 3: Create schema loader**

Create `dev/python/drugbank_parse/schema.py`:

```python
from __future__ import annotations

from pathlib import Path

import yaml

from .models import DrugBankSchema, TableSchema


def default_schema_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "schema"


def load_schema(schema_dir: str | Path | None = None) -> DrugBankSchema:
    base = Path(schema_dir) if schema_dir is not None else default_schema_dir()
    tables_data = _read_yaml(base / "tables.yml")
    fields_data = _read_yaml(base / "fields.yml")

    tables = {}
    for name, definition in tables_data["tables"].items():
        tables[name] = TableSchema(
            name=name,
            description=definition.get("description", ""),
            columns=list(definition["columns"]),
            required=list(definition.get("required", [])),
        )

    return DrugBankSchema(
        version=int(tables_data["version"]),
        tables=tables,
        fields=dict(fields_data.get("fields", {})),
    )


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Schema file does not exist: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Schema file is empty or invalid: {path}")
    return data
```

- [ ] **Step 4: Create public package API**

Create `dev/python/drugbank_parse/__init__.py`:

```python
from .models import ParseResult
from .schema import load_schema

__all__ = ["ParseResult", "load_schema"]
```

- [ ] **Step 5: Run the schema test**

Run:

```powershell
cd dev\python
python -m pytest tests\test_schema.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit the package skeleton**

Run:

```powershell
git add dev\python\pyproject.toml dev\python\drugbank_parse dev\python\tests\test_schema.py
git commit -m "feat: add Python schema loader"
```

---

### Task 3: Implement Profile and Module Resolution

**Files:**
- Create: `dev/python/drugbank_parse/profiles.py`
- Create: `dev/python/tests/test_profiles.py`
- Modify: `dev/python/drugbank_parse/__init__.py`

- [ ] **Step 1: Write failing profile tests**

Create `dev/python/tests/test_profiles.py`:

```python
import pytest

from drugbank_parse.profiles import resolve_modules, resolve_tables


def test_resolve_core_profile_modules():
    assert resolve_modules(profile="core", modules=None) == ["core"]


def test_explicit_modules_override_profile_modules():
    assert resolve_modules(profile="core", modules=["core"]) == ["core"]


def test_unknown_profile_fails_clearly():
    with pytest.raises(ValueError, match="Unknown profile"):
        resolve_modules(profile="not-a-profile", modules=None)


def test_unknown_module_fails_clearly():
    with pytest.raises(ValueError, match="Unknown module"):
        resolve_modules(profile="core", modules=["missing"])


def test_resolve_core_tables():
    assert resolve_tables(["core"]) == [
        "drugs",
        "targets",
        "drug_target",
        "drug_indication",
        "target_drug_indication",
    ]
```

- [ ] **Step 2: Run profile tests and verify they fail**

Run:

```powershell
cd dev\python
python -m pytest tests\test_profiles.py -q
```

Expected: FAIL because `drugbank_parse.profiles` does not exist.

- [ ] **Step 3: Implement profile resolver**

Create `dev/python/drugbank_parse/profiles.py`:

```python
from __future__ import annotations

from pathlib import Path

import yaml

from .schema import default_schema_dir


def load_profiles(schema_dir: str | Path | None = None) -> dict:
    base = Path(schema_dir) if schema_dir is not None else default_schema_dir()
    path = base / "profiles.yml"
    if not path.exists():
        raise FileNotFoundError(f"Profile schema file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Profile schema file is empty or invalid: {path}")
    return data


def resolve_modules(
    profile: str = "core",
    modules: list[str] | None = None,
    schema_dir: str | Path | None = None,
) -> list[str]:
    data = load_profiles(schema_dir)
    known_profiles = data.get("profiles", {})
    known_modules = data.get("modules", {})

    if profile not in known_profiles:
        raise ValueError(f"Unknown profile: {profile}")

    selected = list(modules) if modules is not None else list(known_profiles[profile]["modules"])
    for module in selected:
        if module not in known_modules:
            raise ValueError(f"Unknown module: {module}")
    return selected


def resolve_tables(
    modules: list[str],
    schema_dir: str | Path | None = None,
) -> list[str]:
    data = load_profiles(schema_dir)
    known_modules = data.get("modules", {})
    tables: list[str] = []
    for module in modules:
        if module not in known_modules:
            raise ValueError(f"Unknown module: {module}")
        for table in known_modules[module].get("tables", []):
            if table not in tables:
                tables.append(table)
    return tables
```

- [ ] **Step 4: Export profile helpers from package**

Modify `dev/python/drugbank_parse/__init__.py`:

```python
from .models import ParseResult
from .profiles import resolve_modules, resolve_tables
from .schema import load_schema

__all__ = ["ParseResult", "load_schema", "resolve_modules", "resolve_tables"]
```

- [ ] **Step 5: Run schema and profile tests**

Run:

```powershell
cd dev\python
python -m pytest tests\test_schema.py tests\test_profiles.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit profile resolution**

Run:

```powershell
git add dev\schema\profiles.yml dev\python\drugbank_parse dev\python\tests\test_profiles.py
git commit -m "feat: resolve DrugBank parse profiles"
```

---

### Task 4: Implement Core XML Parser

**Files:**
- Create: `dev/python/drugbank_parse/parser.py`
- Create: `dev/python/tests/conftest.py`
- Create: `dev/python/tests/test_parser_core.py`
- Modify: `dev/python/drugbank_parse/__init__.py`

- [ ] **Step 1: Create test fixtures**

Create `dev/python/tests/conftest.py`:

```python
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture
def root_fixture_xml(project_root: Path) -> Path:
    return project_root / "test-database.xml"
```

- [ ] **Step 2: Write failing parser tests**

Create `dev/python/tests/test_parser_core.py`:

```python
import pytest

from drugbank_parse import parse_drugbank_xml


def test_parse_core_result_contains_expected_tables(root_fixture_xml):
    result = parse_drugbank_xml(root_fixture_xml)

    assert set(result.tables) == {
        "drugs",
        "targets",
        "drug_target",
        "drug_indication",
        "target_drug_indication",
    }


def test_parse_core_extracts_first_drug(root_fixture_xml):
    result = parse_drugbank_xml(root_fixture_xml)

    drugs = result.rows("drugs")
    assert len(drugs) == 1
    assert drugs[0]["drug_id"] == "DB00001"
    assert drugs[0]["drug_name"] == "Lepirudin"
    assert drugs[0]["source"] == "DrugBank"


def test_parse_core_extracts_target_relationships(root_fixture_xml):
    result = parse_drugbank_xml(root_fixture_xml)

    drug_targets = result.rows("drug_target")
    assert drug_targets
    assert all(row["drug_id"] == "DB00001" for row in drug_targets)
    assert all(row["target_id"] for row in drug_targets)


def test_parse_core_builds_denormalized_tdi(root_fixture_xml):
    result = parse_drugbank_xml(root_fixture_xml)

    rows = result.rows("target_drug_indication")
    assert rows
    first = rows[0]
    assert first["drug_id"] == "DB00001"
    assert first["drug_name"] == "Lepirudin"
    assert "Lepirudin" not in first["target_id"]


def test_missing_input_file_fails_clearly(tmp_path):
    missing = tmp_path / "missing.xml"

    with pytest.raises(FileNotFoundError, match="Input XML file does not exist"):
        parse_drugbank_xml(missing)
```

- [ ] **Step 3: Run parser tests and verify they fail**

Run:

```powershell
cd dev\python
python -m pytest tests\test_parser_core.py -q
```

Expected: FAIL because `parse_drugbank_xml` does not exist.

- [ ] **Step 4: Implement parser helpers and core extraction**

Create `dev/python/drugbank_parse/parser.py`:

```python
from __future__ import annotations

from pathlib import Path

from lxml import etree

from .models import ParseResult
from .profiles import resolve_modules, resolve_tables

DRUGBANK_NS = "http://www.drugbank.ca"
NS = {"db": DRUGBANK_NS}
SOURCE = "DrugBank"


def parse_drugbank_xml(
    path: str | Path,
    profile: str = "core",
    modules: list[str] | None = None,
) -> ParseResult:
    xml_path = Path(path)
    if not xml_path.exists():
        raise FileNotFoundError(f"Input XML file does not exist: {xml_path}")

    selected_modules = resolve_modules(profile=profile, modules=modules)
    tables = resolve_tables(selected_modules)
    result = ParseResult(tables={table: [] for table in tables})

    context = etree.iterparse(
        str(xml_path),
        events=("end",),
        tag=f"{{{DRUGBANK_NS}}}drug",
        recover=False,
    )

    for _, drug_node in context:
        _extract_core_drug(drug_node, result)
        drug_node.clear()
        parent = drug_node.getparent()
        while parent is not None and drug_node.getprevious() is not None:
            del parent[0]

    _deduplicate_table(result, "targets", key_fields=("target_id",))
    return result


def _extract_core_drug(drug_node: etree._Element, result: ParseResult) -> None:
    drug_id = _first_text(drug_node, "db:drugbank-id[@primary='true']")
    if not drug_id:
        return

    drug_name = _first_text(drug_node, "db:name")
    indication = _first_text(drug_node, "db:indication")
    inchi = _calculated_property(drug_node, "InChI")

    drug_row = {
        "drug_id": drug_id,
        "drug_name": drug_name,
        "inchi": inchi,
        "source": SOURCE,
    }
    result.add_row("drugs", drug_row)
    result.add_row(
        "drug_indication",
        {
            "drug_id": drug_id,
            "indication": indication,
            "source": SOURCE,
        },
    )

    for target_node in drug_node.xpath("db:targets/db:target", namespaces=NS):
        target_id = _target_id(target_node)
        if not target_id:
            continue

        target_name = _first_text(target_node, "db:name")
        organism = _first_text(target_node, "db:organism")
        gene_name = _first_text(target_node, "db:polypeptide/db:gene-name")

        result.add_row(
            "targets",
            {
                "target_id": target_id,
                "target_name": target_name,
                "gene_name": gene_name,
                "organism": organism,
                "source": SOURCE,
            },
        )
        result.add_row(
            "drug_target",
            {
                "drug_id": drug_id,
                "target_id": target_id,
                "source": SOURCE,
            },
        )
        result.add_row(
            "target_drug_indication",
            {
                "target_id": target_id,
                "gene_name": gene_name,
                "drug_id": drug_id,
                "drug_name": drug_name,
                "inchi": inchi,
                "indication": indication,
                "source": SOURCE,
            },
        )


def _target_id(target_node: etree._Element) -> str:
    polypeptide = target_node.find("db:polypeptide", namespaces=NS)
    if polypeptide is not None:
        return polypeptide.get("id", "") or ""
    return ""


def _first_text(node: etree._Element, xpath: str) -> str:
    values = node.xpath(xpath, namespaces=NS)
    if not values:
        return ""
    value = values[0]
    if isinstance(value, etree._Element):
        return " ".join(value.itertext()).strip()
    return str(value).strip()


def _calculated_property(drug_node: etree._Element, kind: str) -> str:
    properties = drug_node.xpath("db:calculated-properties/db:property", namespaces=NS)
    for property_node in properties:
        property_kind = _first_text(property_node, "db:kind")
        if property_kind == kind:
            return _first_text(property_node, "db:value")
    return ""


def _deduplicate_table(
    result: ParseResult,
    table: str,
    key_fields: tuple[str, ...],
) -> None:
    seen = set()
    rows = []
    for row in result.rows(table):
        key = tuple(row.get(field, "") for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    result.tables[table] = rows
```

- [ ] **Step 5: Export parser API**

Modify `dev/python/drugbank_parse/__init__.py`:

```python
from .models import ParseResult
from .parser import parse_drugbank_xml
from .profiles import resolve_modules, resolve_tables
from .schema import load_schema

__all__ = [
    "ParseResult",
    "load_schema",
    "parse_drugbank_xml",
    "resolve_modules",
    "resolve_tables",
]
```

- [ ] **Step 6: Run parser tests**

Run:

```powershell
cd dev\python
python -m pytest tests\test_parser_core.py -q
```

Expected: PASS. If the fixture contains zero targets or a different first drug, inspect `test-database.xml` and update only the expected assertions to match the fixture facts, not the implementation.

- [ ] **Step 7: Run all current tests**

Run:

```powershell
cd dev\python
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 8: Commit core parser**

Run:

```powershell
git add dev\python\drugbank_parse dev\python\tests
git commit -m "feat: parse DrugBank core XML tables"
```

---

### Task 5: Implement Schema-Aware CSV Exporter

**Files:**
- Create: `dev/python/drugbank_parse/exporters.py`
- Create: `dev/python/tests/test_exporters.py`
- Modify: `dev/python/drugbank_parse/__init__.py`

- [ ] **Step 1: Write failing exporter tests**

Create `dev/python/tests/test_exporters.py`:

```python
import csv

from drugbank_parse import parse_drugbank_xml, write_drugbank_tables


def test_write_drugbank_tables_creates_core_csvs(root_fixture_xml, tmp_path):
    result = parse_drugbank_xml(root_fixture_xml)

    written = write_drugbank_tables(result, tmp_path)

    assert sorted(path.name for path in written) == [
        "drug_indication.csv",
        "drug_target.csv",
        "drugs.csv",
        "target_drug_indication.csv",
        "targets.csv",
    ]


def test_write_drugbank_tables_uses_schema_column_order(root_fixture_xml, tmp_path):
    result = parse_drugbank_xml(root_fixture_xml)

    write_drugbank_tables(result, tmp_path)

    with (tmp_path / "drugs.csv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)

    assert header == ["drug_id", "drug_name", "inchi", "source"]
```

- [ ] **Step 2: Run exporter tests and verify they fail**

Run:

```powershell
cd dev\python
python -m pytest tests\test_exporters.py -q
```

Expected: FAIL because `write_drugbank_tables` does not exist.

- [ ] **Step 3: Implement exporter**

Create `dev/python/drugbank_parse/exporters.py`:

```python
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
```

- [ ] **Step 4: Export writer from package API**

Modify `dev/python/drugbank_parse/__init__.py`:

```python
from .exporters import write_drugbank_tables
from .models import ParseResult
from .parser import parse_drugbank_xml
from .profiles import resolve_modules, resolve_tables
from .schema import load_schema

__all__ = [
    "ParseResult",
    "load_schema",
    "parse_drugbank_xml",
    "resolve_modules",
    "resolve_tables",
    "write_drugbank_tables",
]
```

- [ ] **Step 5: Run exporter tests and full test suite**

Run:

```powershell
cd dev\python
python -m pytest tests\test_exporters.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit exporter**

Run:

```powershell
git add dev\python\drugbank_parse dev\python\tests\test_exporters.py
git commit -m "feat: export DrugBank core tables"
```

---

### Task 6: Add CLI Wrapper

**Files:**
- Create: `dev/python/drugbank_parse/cli.py`
- Create: `dev/python/tests/test_cli.py`

- [ ] **Step 1: Write failing CLI smoke test**

Create `dev/python/tests/test_cli.py`:

```python
from drugbank_parse.cli import main


def test_cli_writes_core_tables(root_fixture_xml, tmp_path):
    exit_code = main([
        "--input",
        str(root_fixture_xml),
        "--profile",
        "core",
        "--outdir",
        str(tmp_path),
    ])

    assert exit_code == 0
    assert (tmp_path / "drugs.csv").exists()
    assert (tmp_path / "target_drug_indication.csv").exists()
```

- [ ] **Step 2: Run CLI test and verify it fails**

Run:

```powershell
cd dev\python
python -m pytest tests\test_cli.py -q
```

Expected: FAIL because `drugbank_parse.cli` does not exist.

- [ ] **Step 3: Implement CLI**

Create `dev/python/drugbank_parse/cli.py`:

```python
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
```

- [ ] **Step 4: Register console script**

Update `dev/python/pyproject.toml`:

```toml
[project.scripts]
drugbank-parse = "drugbank_parse.cli:main"
```

- [ ] **Step 5: Run CLI test and full test suite**

Run:

```powershell
cd dev\python
python -m pytest tests\test_cli.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Manually smoke test CLI against fixture**

Run:

```powershell
cd dev\python
python -m drugbank_parse.cli --input ..\..\test-database.xml --profile core --outdir ..\tmp_core_output
```

Expected: prints five CSV paths under `dev\tmp_core_output`.

- [ ] **Step 7: Remove manual smoke output**

Run:

```powershell
Remove-Item ..\tmp_core_output -Recurse -Force
```

Expected: temporary output directory is removed. Verify the resolved path is `D:\Study\Project\DrugBank_parse\dev\tmp_core_output` before running the command.

- [ ] **Step 8: Commit CLI wrapper**

Run:

```powershell
git add dev\python\drugbank_parse\cli.py dev\python\tests\test_cli.py dev\python\pyproject.toml
git commit -m "feat: add DrugBank parser CLI"
```

---

### Task 7: Add Expected Fixture CSVs

**Files:**
- Create: `dev/fixtures/expected/core/drugs.csv`
- Create: `dev/fixtures/expected/core/targets.csv`
- Create: `dev/fixtures/expected/core/drug_target.csv`
- Create: `dev/fixtures/expected/core/drug_indication.csv`
- Create: `dev/fixtures/expected/core/target_drug_indication.csv`
- Modify: `dev/python/tests/test_exporters.py`

- [ ] **Step 1: Generate expected fixture outputs from the implemented parser**

Run:

```powershell
cd dev\python
python -m drugbank_parse.cli --input ..\..\test-database.xml --profile core --outdir ..\fixtures\expected\core
```

Expected: five CSV files are written under `dev\fixtures\expected\core`.

- [ ] **Step 2: Inspect expected CSVs before accepting them**

Run:

```powershell
Get-Content ..\fixtures\expected\core\drugs.csv
Get-Content ..\fixtures\expected\core\targets.csv
Get-Content ..\fixtures\expected\core\drug_target.csv
Get-Content ..\fixtures\expected\core\drug_indication.csv
Get-Content ..\fixtures\expected\core\target_drug_indication.csv
```

Expected: headers match schema; `drugs.csv` contains `DB00001,Lepirudin`; target and relationship files are non-empty. If any row is clearly wrong, fix parser code before keeping these files.

- [ ] **Step 3: Add exact fixture comparison test**

Modify `dev/python/tests/test_exporters.py` by adding:

```python
from pathlib import Path


def test_exported_core_csvs_match_expected_fixture(root_fixture_xml, tmp_path, project_root):
    result = parse_drugbank_xml(root_fixture_xml)
    write_drugbank_tables(result, tmp_path)

    expected_dir = project_root / "dev" / "fixtures" / "expected" / "core"
    for expected_path in expected_dir.glob("*.csv"):
        actual_path = tmp_path / expected_path.name
        assert actual_path.read_text(encoding="utf-8") == expected_path.read_text(encoding="utf-8")
```

If `Path` is unused after editing, remove the import.

- [ ] **Step 4: Run exporter tests and full suite**

Run:

```powershell
cd dev\python
python -m pytest tests\test_exporters.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit fixture expectations**

Run:

```powershell
git add dev\fixtures\expected\core dev\python\tests\test_exporters.py
git commit -m "test: add core fixture CSV expectations"
```

---

### Task 8: Add Minimal Developer Documentation

**Files:**
- Create: `dev/README.md`
- Modify: `README.md`

- [ ] **Step 1: Create dev README**

Create `dev/README.md`:

```markdown
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
```

- [ ] **Step 2: Update root README to point at dev rewrite**

Add this section near the top of `README.md`, after the opening blockquote:

```markdown
## Current Rewrite

The new implementation is being developed under `dev/`. It is package-first, schema-driven, and designed for low-memory parsing of full DrugBank XML files. See `dev/README.md` for the Python core parser workflow.
```

- [ ] **Step 3: Run documentation-related smoke checks**

Run:

```powershell
Test-Path dev\README.md
Select-String -Path README.md -Pattern "Current Rewrite"
```

Expected: both commands show the new documentation exists.

- [ ] **Step 4: Commit docs**

Run:

```powershell
git add README.md dev\README.md
git commit -m "docs: document dev Python core parser"
```

---

### Task 9: Final Verification for Phase 1

**Files:**
- No new files.
- Verify all files created or modified by Tasks 1-8.

- [ ] **Step 1: Run full Python test suite**

Run:

```powershell
cd dev\python
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 2: Run package import smoke test**

Run:

```powershell
cd dev\python
python -c "from drugbank_parse import parse_drugbank_xml, write_drugbank_tables; print(parse_drugbank_xml, write_drugbank_tables)"
```

Expected: prints function objects without import errors.

- [ ] **Step 3: Run CLI smoke test**

Run:

```powershell
cd dev\python
python -m drugbank_parse.cli --input ..\..\test-database.xml --profile core --outdir ..\tmp_core_output
```

Expected: prints paths for `drugs.csv`, `targets.csv`, `drug_target.csv`, `drug_indication.csv`, and `target_drug_indication.csv`.

- [ ] **Step 4: Inspect smoke output**

Run:

```powershell
Get-ChildItem ..\tmp_core_output
Get-Content ..\tmp_core_output\drugs.csv
```

Expected: five CSV files exist and `drugs.csv` includes the `drug_id,drug_name,inchi,source` header.

- [ ] **Step 5: Remove smoke output**

Run:

```powershell
Remove-Item ..\tmp_core_output -Recurse -Force
```

Expected: temporary output directory is removed. Confirm the resolved path is inside `D:\Study\Project\DrugBank_parse\dev` before running this command.

- [ ] **Step 6: Check git status**

Run:

```powershell
git status --short
```

Expected: only pre-existing unrelated files remain untracked, such as `.idea/`, `dev/DrugBank_prase_xml2.R`, and `vR/getTargetsFromXML.R`. There should be no unstaged changes from Phase 1.

- [ ] **Step 7: Record next recommended plan**

Create the next plan only after Phase 1 is complete. The next plan should be `docs/superpowers/plans/YYYY-MM-DD-r-core-package.md` and should implement the R package against the same schema and expected core fixture outputs.
