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
