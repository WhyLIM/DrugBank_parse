import pytest

from drugbank_parse.models import ParseResult


def test_parse_result_rejects_rows_for_uninitialized_tables():
    result = ParseResult(tables={"drugs": []})

    with pytest.raises(KeyError, match="targets"):
        result.add_row("targets", {"target_id": "P00734"})
