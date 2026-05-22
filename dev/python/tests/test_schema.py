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
