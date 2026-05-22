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
