"""Measure forced demo runs without mixing volatile metrics into stable outputs."""

import argparse
import json
import platform
import statistics
import sys
import tempfile
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.config import (  # noqa: E402
    DEMO_DEFAULT_ROWS,
    DEMO_DEFAULT_SEED,
    build_demo_paths,
)
from src.pipeline import run_pipeline  # noqa: E402

DEFAULT_OUTPUT = BASE_DIR / "docs" / "performance_baseline.json"


def benchmark_demo(runs: int) -> dict:
    if runs < 3:
        raise ValueError("El baseline requiere al menos 3 ejecuciones.")

    measurements = []
    with tempfile.TemporaryDirectory(prefix="miami-etl-benchmark-") as temp_dir:
        paths = build_demo_paths(Path(temp_dir) / "demo")
        for run_number in range(1, runs + 1):
            result = run_pipeline(
                mode="demo",
                paths=paths,
                demo_rows=DEMO_DEFAULT_ROWS,
                demo_seed=DEMO_DEFAULT_SEED,
                incremental=False,
            )
            measurements.append({
                "run": run_number,
                "elapsed_seconds": result["runtime"]["elapsed_seconds"],
                "peak_memory_mb": result["runtime"]["peak_memory_mb"],
            })

    elapsed = [row["elapsed_seconds"] for row in measurements]
    memory = [row["peak_memory_mb"] for row in measurements]
    return {
        "baseline_version": "1.0.0",
        "recorded_on": date.today().isoformat(),
        "mode": "demo_forced",
        "rows": DEMO_DEFAULT_ROWS,
        "seed": DEMO_DEFAULT_SEED,
        "environment": {
            "os": platform.system(),
            "python": platform.python_version(),
            "processor": platform.processor() or "not reported",
        },
        "budgets": {
            "max_elapsed_seconds": 10.0,
            "max_peak_memory_mb": 256.0,
        },
        "summary": {
            "runs": runs,
            "median_elapsed_seconds": round(statistics.median(elapsed), 4),
            "max_elapsed_seconds": round(max(elapsed), 4),
            "median_peak_memory_mb": round(statistics.median(memory), 2),
            "max_peak_memory_mb": round(max(memory), 2),
        },
        "measurements": measurements,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    baseline = benchmark_demo(args.runs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Baseline guardado: {args.output}")
    print(json.dumps(baseline["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
