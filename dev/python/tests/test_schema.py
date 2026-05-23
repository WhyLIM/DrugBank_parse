import shutil

from drugbank_parse.schema import default_schema_dir, load_schema


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


def test_default_schema_dir_uses_packaged_schema_data():
    schema_dir = default_schema_dir()

    assert schema_dir.name == "schema_data"
    assert (schema_dir / "tables.yml").exists()
    assert (schema_dir / "fields.yml").exists()
    assert (schema_dir / "profiles.yml").exists()


def test_load_schema_accepts_schema_dir_override(project_root, tmp_path):
    schema_dir = tmp_path / "schema"
    shutil.copytree(project_root / "dev" / "schema", schema_dir)

    schema = load_schema(schema_dir=schema_dir)

    assert schema.version == 1
    assert "drugs" in schema.tables
