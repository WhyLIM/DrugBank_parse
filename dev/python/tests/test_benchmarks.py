from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_python_benchmark(project_root: Path):
    path = project_root / "dev" / "benchmarks" / "python_benchmark.py"
    spec = importlib.util.spec_from_file_location("python_benchmark", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_python_benchmark_writes_metrics_json(project_root, root_fixture_xml, tmp_path):
    benchmark = load_python_benchmark(project_root)
    output_dir = tmp_path / "csv"
    metrics_path = tmp_path / "metrics.json"

    metrics = benchmark.run_benchmark(
        input_path=root_fixture_xml,
        outdir=output_dir,
        metrics_path=metrics_path,
        profile="core",
    )

    assert metrics_path.exists()
    saved = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert saved == metrics
    assert saved["input_path"] == str(root_fixture_xml)
    assert saved["profile"] == "core"
    assert saved["output_dir"] == str(output_dir)
    assert saved["elapsed_seconds"] >= 0
    assert saved["table_rows"] == {
        "drugs": 2,
        "targets": 3,
        "drug_target": 3,
        "drug_indication": 2,
        "target_drug_indication": 3,
    }
    assert sorted(saved["written_files"]) == [
        "drug_indication.csv",
        "drug_target.csv",
        "drugs.csv",
        "target_drug_indication.csv",
        "targets.csv",
    ]
