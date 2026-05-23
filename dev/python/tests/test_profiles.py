import pytest

from drugbank_parse.profiles import resolve_modules, resolve_tables


def test_resolve_core_profile_modules():
    assert resolve_modules(profile="core", modules=None) == ["core"]


def test_explicit_modules_override_profile_modules():
    assert resolve_modules(profile="core", modules=["core"]) == ["core"]


def test_unknown_profile_fails_clearly():
    with pytest.raises(ValueError, match="Unknown profile"):
        resolve_modules(profile="not-a-profile", modules=None)


def test_unknown_module_fails_clearly():
    with pytest.raises(ValueError, match="Unknown module"):
        resolve_modules(profile="core", modules=["missing"])


def test_resolve_core_tables():
    assert resolve_tables(["core"]) == [
        "drugs",
        "targets",
        "drug_target",
        "drug_indication",
        "target_drug_indication",
    ]
