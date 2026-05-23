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


def test_exported_core_csvs_match_expected_fixture(root_fixture_xml, tmp_path, project_root):
    expected_filenames = {
        "drugs.csv",
        "targets.csv",
        "drug_target.csv",
        "drug_indication.csv",
        "target_drug_indication.csv",
    }
    result = parse_drugbank_xml(root_fixture_xml)
    write_drugbank_tables(result, tmp_path)

    expected_dir = project_root / "dev" / "fixtures" / "expected" / "core"
    assert expected_dir.is_dir()
    assert {path.name for path in expected_dir.glob("*.csv")} == expected_filenames
    assert {path.name for path in tmp_path.glob("*.csv")} == expected_filenames

    for filename in expected_filenames:
        expected_path = expected_dir / filename
        actual_path = tmp_path / filename
        assert actual_path.read_text(encoding="utf-8") == expected_path.read_text(encoding="utf-8")
