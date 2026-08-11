"""Run the final C3-Lite portfolio verification gate."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
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

PYTHON = Path(sys.executable)
BASELINE_PATH = BASE_DIR / "docs" / "performance_baseline.json"
REPORT_PATH = BASE_DIR / "docs" / "c3_lite_verification.md"


def _run_command(label: str, command: list[str]) -> dict:
    started = time.perf_counter()
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if result.returncode:
        details = (result.stdout + "\n" + result.stderr).strip()
        raise RuntimeError(f"{label} falló:\n{details}")
    evidence = (result.stdout.strip().splitlines() or ["OK"])[-1]
    evidence = evidence.replace(str(BASE_DIR), ".")
    return {
        "check": label,
        "status": "APROBADO",
        "evidence": evidence,
        "elapsed_seconds": round(elapsed, 2),
    }


def _stable_hashes(paths) -> dict[str, str]:
    return {
        str(path.relative_to(paths.publication_root)).replace("\\", "/"): (
            hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for path in paths.stable_outputs()
    }


def _verify_demo_reproducibility() -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory(prefix="miami-etl-c3-") as temp_dir:
        paths = build_demo_paths(Path(temp_dir) / "demo")
        first = run_pipeline(
            mode="demo",
            paths=paths,
            demo_rows=DEMO_DEFAULT_ROWS,
            demo_seed=DEMO_DEFAULT_SEED,
            incremental=False,
        )
        first_hashes = _stable_hashes(paths)
        second = run_pipeline(
            mode="demo",
            paths=paths,
            demo_rows=DEMO_DEFAULT_ROWS,
            demo_seed=DEMO_DEFAULT_SEED,
            incremental=False,
        )
        if _stable_hashes(paths) != first_hashes:
            raise AssertionError("Dos reconstrucciones demo produjeron hashes distintos.")
        cached = run_pipeline(
            mode="demo",
            paths=paths,
            demo_rows=DEMO_DEFAULT_ROWS,
            demo_seed=DEMO_DEFAULT_SEED,
            incremental=True,
        )
        if cached["status"] != "unchanged":
            raise AssertionError("La tercera ejecución no detectó el snapshot sin cambios.")
        metrics = {
            "forced_max_seconds": max(
                first["runtime"]["elapsed_seconds"],
                second["runtime"]["elapsed_seconds"],
            ),
            "forced_max_memory_mb": max(
                first["runtime"]["peak_memory_mb"],
                second["runtime"]["peak_memory_mb"],
            ),
            "cached_seconds": cached["runtime"]["elapsed_seconds"],
            "cached_memory_mb": cached["runtime"]["peak_memory_mb"],
            "stable_files": len(first_hashes),
        }
        check = {
            "check": "Demo determinista e incremental",
            "status": "APROBADO",
            "evidence": (
                f"{len(first_hashes)} archivos estables; "
                f"run_id={cached['runtime']['run_id']}; tercera ejecución unchanged"
            ),
            "elapsed_seconds": round(
                first["runtime"]["elapsed_seconds"]
                + second["runtime"]["elapsed_seconds"]
                + cached["runtime"]["elapsed_seconds"],
                2,
            ),
        }
        return check, metrics


def _validate_performance(metrics: dict) -> dict:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    budgets = baseline["budgets"]
    if metrics["forced_max_seconds"] > budgets["max_elapsed_seconds"]:
        raise AssertionError("La demo excede el presupuesto absoluto de tiempo.")
    if metrics["forced_max_memory_mb"] > budgets["max_peak_memory_mb"]:
        raise AssertionError("La demo excede el presupuesto absoluto de memoria.")
    return {
        "check": "Presupuesto de rendimiento",
        "status": "APROBADO",
        "evidence": (
            f"máximo {metrics['forced_max_seconds']:.2f}s y "
            f"{metrics['forced_max_memory_mb']:.2f} MiB; "
            f"presupuesto {budgets['max_elapsed_seconds']:.0f}s/"
            f"{budgets['max_peak_memory_mb']:.0f} MiB"
        ),
        "elapsed_seconds": 0,
    }


def _write_report(checks: list[dict], metrics: dict, include_full: bool) -> None:
    rows = "\n".join(
        f"| {item['check']} | {item['status']} | {item['evidence']} |"
        for item in checks
    )
    report = f"""# Verificación C3-Lite

Estado: **APROBADO**.
Fecha: {date.today().isoformat()}.

Esta puerta reúne las comprobaciones técnicas finales del proyecto sin afirmar que la demo sintética reproduce la distribución comercial del raw educativo.

| Control | Estado | Evidencia |
|---|---|---|
{rows}

## Rendimiento observado

- Reconstrucción demo más lenta: {metrics['forced_max_seconds']:.4f} segundos.
- Pico máximo de memoria: {metrics['forced_max_memory_mb']:.2f} MiB.
- Ejecución incremental: {metrics['cached_seconds']:.4f} segundos y {metrics['cached_memory_mb']:.2f} MiB.
- Archivos deterministas comparados: {metrics['stable_files']}.

## Alcance

- Pipeline full local incluido: {'sí' if include_full else 'no; raw privado no disponible en CI'}.
- Pipeline demo público reconstruido dos veces y luego validado en modo incremental.
- La CI repite esta puerta en Python 3.12, 3.13 y 3.14 sobre Windows.
- Los presupuestos son guardrails de regresión técnica, no benchmarks universales entre equipos.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-full", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--enforce-clean-generated", action="store_true")
    args = parser.parse_args(argv)

    checks = [
        _run_command("Ruff", [str(PYTHON), "-m", "ruff", "check", "."]),
        _run_command("Pytest", [str(PYTHON), "-m", "pytest", "-q"]),
    ]
    demo_check, metrics = _verify_demo_reproducibility()
    checks.append(demo_check)
    checks.append(_validate_performance(metrics))

    run_pipeline(mode="demo", incremental=False)
    checks.append(
        _run_command(
            "Publicación demo",
            [str(PYTHON), "scripts/validate_publication.py", "--mode", "demo"],
        )
    )

    if args.include_full:
        full = run_pipeline(mode="full", incremental=False)
        cached_full = run_pipeline(mode="full", incremental=True)
        if full["runtime"]["run_id"] != cached_full["runtime"]["run_id"]:
            raise AssertionError("El run_id full cambió sin cambios de entrada.")
        if cached_full["status"] != "unchanged":
            raise AssertionError("El pipeline full no activó incrementalidad.")
        checks.append({
            "check": "Pipeline full local",
            "status": "APROBADO",
            "evidence": (
                f"run_id={cached_full['runtime']['run_id']}; "
                f"{len(full['customers_miami']):,} clientes Miami"
            ),
            "elapsed_seconds": full["runtime"]["elapsed_seconds"],
        })

    checks.append(
        _run_command(
            "Notebook ejecutado",
            [str(PYTHON), "scripts/render_notebook.py"],
        )
    )
    checks.append(
        _run_command(
            "Publicación full",
            [str(PYTHON), "scripts/validate_publication.py", "--mode", "full"],
        )
    )

    if args.enforce_clean_generated:
        checks.append(
            _run_command(
                "Outputs versionados sin drift",
                [
                    "git",
                    "diff",
                    "--exit-code",
                    "--",
                    "data/demo",
                    "data/final",
                    "docs/assets",
                    "docs/data_quality_report.md",
                    "notebooks/01_miami_business_case.ipynb",
                ],
            )
        )

    if args.write_report:
        _write_report(checks, metrics, args.include_full)

    print("C3-Lite APROBADO")
    for item in checks:
        print(f"- {item['check']}: {item['status']} — {item['evidence']}")


if __name__ == "__main__":
    main()
