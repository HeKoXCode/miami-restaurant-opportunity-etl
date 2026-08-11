from hashlib import sha256

from src.config import PII_COLUMNS, build_demo_paths
from src.pipeline import run_pipeline


def _output_hashes(paths):
    return {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in paths.output_files()
    }


def test_demo_pipeline_runs_end_to_end_in_isolated_paths(tmp_path):
    paths = build_demo_paths(tmp_path / "demo")
    outputs = run_pipeline(
        mode="demo",
        paths=paths,
        demo_rows=320,
        demo_seed=12345,
    )

    assert len(outputs["customers_clean"]) < 320
    assert not outputs["customers_miami"].empty
    assert set(outputs["preference_opportunity"]["customer_preference"]) == {
        "Mariscos",
        "Pescado",
        "Carnes",
        "Vegetariano",
        "Vegano",
        "Otro",
    }
    assert not set(PII_COLUMNS) & set(outputs["customers_clean"].columns)
    assert all(path.exists() for path in paths.output_files())


def test_demo_pipeline_is_deterministic(tmp_path):
    paths = build_demo_paths(tmp_path / "demo")
    run_pipeline(mode="demo", paths=paths, demo_rows=320, demo_seed=12345)
    first_hashes = _output_hashes(paths)

    run_pipeline(mode="demo", paths=paths, demo_rows=320, demo_seed=12345)

    assert _output_hashes(paths) == first_hashes
