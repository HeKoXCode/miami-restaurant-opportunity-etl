import json
import os

import pytest

from src.config import build_demo_paths
from src.pipeline import run_pipeline
from src.runtime import atomic_publish


def test_incremental_pipeline_skips_unchanged_snapshot(tmp_path):
    paths = build_demo_paths(tmp_path / "demo")

    first = run_pipeline(
        mode="demo",
        paths=paths,
        demo_rows=320,
        demo_seed=12345,
    )
    second = run_pipeline(
        mode="demo",
        paths=paths,
        demo_rows=320,
        demo_seed=12345,
    )

    manifest = json.loads(paths.pipeline_manifest.read_text(encoding="utf-8"))
    assert first["status"] == "rebuilt"
    assert second["status"] == "unchanged"
    assert first["runtime"]["run_id"] == second["runtime"]["run_id"]
    assert manifest["pipeline_version"] == "2.0.0"
    assert len(manifest["inputs"]) == 3
    assert len(manifest["outputs"]) == 12


def test_atomic_publish_restores_every_prior_file_on_failure(tmp_path, monkeypatch):
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text("old-first\n", encoding="utf-8")
    second.write_text("old-second\n", encoding="utf-8")
    real_replace = os.replace

    def fail_second_temporary(source, destination):
        if str(source).endswith(".tmp") and destination == second:
            raise OSError("simulated publication failure")
        return real_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_second_temporary)

    with pytest.raises(OSError, match="simulated publication failure"):
        atomic_publish({first: b"new-first\n", second: b"new-second\n"})

    assert first.read_text(encoding="utf-8") == "old-first\n"
    assert second.read_text(encoding="utf-8") == "old-second\n"
