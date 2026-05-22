from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture
def root_fixture_xml(project_root: Path) -> Path:
    return project_root / "test-database.xml"
