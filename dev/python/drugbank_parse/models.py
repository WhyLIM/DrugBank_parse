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
        if table not in self.tables:
            raise KeyError(f"Table is not enabled for this parse result: {table}")
        self.tables[table].append(row)

    def rows(self, table: str) -> list[dict[str, str]]:
        return self.tables.get(table, [])
