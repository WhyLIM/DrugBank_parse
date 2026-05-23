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
        if "core" in selected_modules:
            _extract_core_drug(drug_node, result)
        while drug_node.getprevious() is not None:
            del drug_node.getparent()[0]
        drug_node.clear()

    if "targets" in result.tables:
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
