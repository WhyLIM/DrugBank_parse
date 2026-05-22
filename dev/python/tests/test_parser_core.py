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
    assert len(drugs) == 2
    assert drugs[0]["drug_id"] == "DB00001"
    assert drugs[0]["drug_name"] == "Lepirudin"
    assert drugs[0]["source"] == "DrugBank"


def test_parse_core_extracts_target_relationships(root_fixture_xml):
    result = parse_drugbank_xml(root_fixture_xml)

    drug_targets = result.rows("drug_target")
    assert len(drug_targets) == 3
    assert {(row["drug_id"], row["target_id"]) for row in drug_targets} == {
        ("DB00001", "P00734"),
        ("DB00014", "P22888"),
        ("DB00014", "P30968"),
    }


def test_parse_core_builds_denormalized_tdi(root_fixture_xml):
    result = parse_drugbank_xml(root_fixture_xml)

    rows = result.rows("target_drug_indication")
    assert len(rows) == 3
    assert {(row["drug_id"], row["target_id"]) for row in rows} == {
        ("DB00001", "P00734"),
        ("DB00014", "P22888"),
        ("DB00014", "P30968"),
    }

    first = rows[0]
    assert first["drug_id"] == "DB00001"
    assert first["drug_name"] == "Lepirudin"
    assert "Lepirudin" not in first["target_id"]

    db00014_rows = {row["target_id"]: row for row in rows if row["drug_id"] == "DB00014"}
    assert {row["drug_name"] for row in db00014_rows.values()} == {"Goserelin"}
    assert db00014_rows["P22888"]["gene_name"] == "LHCGR"
    assert db00014_rows["P30968"]["gene_name"] == "GNRHR"


def test_missing_input_file_fails_clearly(tmp_path):
    missing = tmp_path / "missing.xml"

    with pytest.raises(FileNotFoundError, match="Input XML file does not exist"):
        parse_drugbank_xml(missing)
