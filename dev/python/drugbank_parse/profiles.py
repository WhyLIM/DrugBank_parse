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
