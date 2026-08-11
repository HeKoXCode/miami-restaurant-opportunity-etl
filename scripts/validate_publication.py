"""Validate full publication evidence or deterministic demo outputs."""

import argparse
import json
import re
from csv import DictReader
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def read_csv(relative_path):
    path = BASE_DIR / relative_path
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(DictReader(file))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def format_integer(value):
    rounded = Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"{int(rounded):,}".replace(",", ".")


def format_percent(value):
    return f"{float(value):.1%}".replace(".", ",").replace("%", " %")


def validate_readme_metrics():
    readme = (BASE_DIR / "README.md").read_text(encoding="utf-8")
    customers = read_csv("data/final/customers_miami.csv")
    customer_value = read_csv("data/final/customer_value_miami.csv")
    opportunity = read_csv("data/final/preference_opportunity_miami.csv")

    total_spend = sum(
        (Decimal(row["gasto_periodo_estimado"]) for row in customers),
        Decimal(0),
    )
    premium = next(
        row
        for row in customer_value
        if row["dimension"] == "Membresia premium" and row["segment"] == "Sí"
    )
    high_value = next(
        row
        for row in customer_value
        if row["dimension"] == "Estrato socioeconomico"
        and row["segment"] == "Muy Alto"
    )
    top_spend = max(opportunity, key=lambda row: Decimal(row["estimated_period_spend"]))
    strongest_gap = max(
        (row for row in opportunity if row["preference_data_quality"] != "Baja"),
        key=lambda row: Decimal(row["demand_coverage_index"]),
    )

    expected_fragments = [
        f"**{format_integer(len(customers))} clientes de Miami**",
        f"**{format_integer(total_spend)} unidades de gasto estimado por período**",
        f"| Clientes premium | {format_percent(premium['customer_share'])} de la base |",
        f"| Gasto concentrado en premium | {format_percent(premium['spend_share'])} |",
        f"| Clientes de estrato Muy Alto | {format_percent(high_value['customer_share'])} |",
        f"| Gasto concentrado en estrato Muy Alto | {format_percent(high_value['spend_share'])} |",
        "| Preferencia con mayor gasto estimado "
        f"| {top_spend['customer_preference']} — "
        f"{format_integer(top_spend['estimated_period_spend'])} unidades |",
        "| Mayor brecha demanda/cobertura observada "
        f"| {strongest_gap['customer_preference']} |",
    ]
    for fragment in expected_fragments:
        require(fragment in readme, f"El README no coincide con los datos: {fragment}")


def validate_notebook():
    notebook_path = BASE_DIR / "notebooks" / "01_miami_business_case.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    outputs = [output for cell in code_cells for output in cell.get("outputs", [])]

    require(len(notebook["cells"]) == 27, "El notebook debe conservar 27 celdas.")
    require(len(code_cells) == 10, "El notebook debe conservar 10 celdas de código.")
    require(
        all(cell.get("execution_count") is not None for cell in code_cells),
        "Todas las celdas de código deben quedar ejecutadas.",
    )
    require(
        not any(output.get("output_type") == "error" for output in outputs),
        "El notebook contiene un output de error.",
    )
    require(
        sum("image/png" in output.get("data", {}) for output in outputs) == 6,
        "El notebook debe contener exactamente 6 gráficos PNG.",
    )
    require(
        all("execution" not in cell.get("metadata", {}) for cell in code_cells),
        "El notebook contiene timestamps de ejecución no deterministas.",
    )
    serialized_outputs = json.dumps(outputs, ensure_ascii=False)
    require(
        not re.search(r" at 0x[0-9a-fA-F]+", serialized_outputs),
        "El notebook contiene una dirección de memoria no determinista.",
    )
    notebook_source = "\n".join(
        "".join(cell.get("source", [])) for cell in notebook["cells"]
    )
    require(
        "data/clean" not in notebook_source
        and "docs/data_quality_report.csv" not in notebook_source,
        "El notebook consume una capa anterior a data/final.",
    )


def validate_privacy(mode):
    forbidden_columns = {
        "nombre",
        "apellido",
        "telefono_contacto",
        "teléfono_contacto",
        "email",
        "correo_electronico",
    }
    prefix = "data" if mode == "full" else "data/demo"
    for relative_path in (
        f"{prefix}/clean/customers_clean.csv",
        f"{prefix}/final/customers_miami.csv",
    ):
        rows = read_csv(relative_path)
        require(rows, f"El output está vacío: {relative_path}")
        columns = {column.casefold() for column in rows[0]}
        require(
            columns.isdisjoint(forbidden_columns),
            f"El output contiene columnas con PII: {relative_path}",
        )

    gitignore = (BASE_DIR / ".gitignore").read_text(encoding="utf-8")
    require("data/raw/customers_raw.csv" in gitignore, "El raw privado no está ignorado.")
    require(".env" in gitignore, "El archivo .env no está ignorado.")


def validate_demo_outputs():
    demo_root = BASE_DIR / "data" / "demo"
    expected_files = {
        "README.md",
        "raw/customers_demo_raw.csv",
        "staging/customers_staging.csv",
        "staging/yelp_restaurants_staging.csv",
        "clean/customers_clean.csv",
        "clean/yelp_restaurants_clean.csv",
        "final/customers_miami.csv",
        "final/customer_value_miami.csv",
        "final/preference_opportunity_miami.csv",
        "final/restaurant_competition_miami.csv",
        "final/preference_sensitivity_miami.csv",
        "final/data_quality_report.csv",
        "final/data_rejections.csv",
        "final/pipeline_manifest.json",
        "docs/data_quality_report.md",
        "docs/generation_metadata.json",
    }
    actual_files = {
        str(path.relative_to(demo_root)).replace("\\", "/")
        for path in demo_root.rglob("*")
        if path.is_file()
    }
    require(
        actual_files == expected_files,
        (
            f"Archivos demo inesperados. Faltan={sorted(expected_files - actual_files)}; "
            f"sobran={sorted(actual_files - expected_files)}"
        ),
    )

    metadata = json.loads(
        (demo_root / "docs" / "generation_metadata.json").read_text(encoding="utf-8")
    )
    require(metadata.get("fully_synthetic") is True, "La demo no declara origen sintético.")
    require(metadata.get("seed") == 20260713, "La semilla demo no es la documentada.")
    require(metadata.get("rows") == 750, "La demo versionada no contiene 750 filas raw.")

    manifest = json.loads(
        (demo_root / "final" / "pipeline_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    require(manifest.get("pipeline_version") == "2.0.0", "Pipeline sin versión C1.")
    require(manifest.get("schema_version") == "1.1.0", "Schema demo inesperado.")
    require(len(manifest.get("inputs", [])) == 3, "Manifest sin tres fuentes.")
    require(len(manifest.get("outputs", [])) == 12, "Manifest incompleto.")

    raw = read_csv("data/demo/raw/customers_demo_raw.csv")
    require(len(raw) == 750, "El raw demo debe contener 750 clientes.")
    require(
        all(row["nombre"].startswith("Cliente Demo ") for row in raw),
        "El raw demo contiene nombres que no siguen el patrón sintético.",
    )
    require(
        all(row["correo_electronico"].endswith("@example.invalid") for row in raw),
        "El raw demo contiene correos fuera del dominio reservado.",
    )
    require(
        all("-555-0" in row["telefono_contacto"] for row in raw),
        "El raw demo contiene teléfonos fuera del rango reservado 555-01xx.",
    )


def validate_advanced_marts(mode):
    prefix = "data" if mode == "full" else "data/demo"
    opportunity = read_csv(f"{prefix}/final/preference_opportunity_miami.csv")
    competition = read_csv(f"{prefix}/final/restaurant_competition_miami.csv")
    sensitivity = read_csv(f"{prefix}/final/preference_sensitivity_miami.csv")
    require(len(competition) == 30, "Competencia debe tener 6 preferencias x 5 precios.")
    require(len(sensitivity) == 18, "Sensibilidad debe tener 6 x 3 escenarios.")
    require(
        {row["price_level"] for row in competition} == {"0", "1", "2", "3", "4"},
        "Faltan niveles en competencia por precio.",
    )
    require(
        {row["scenario"] for row in sensitivity}
        == {"Conservador", "Base", "Exploratorio"},
        "Faltan escenarios de sensibilidad.",
    )
    base_signals = {
        row["customer_preference"]: row["coverage_signal"]
        for row in sensitivity
        if row["scenario"] == "Base"
    }
    published_signals = {
        row["customer_preference"]: row["coverage_signal"]
        for row in opportunity
    }
    require(
        base_signals == published_signals,
        "El escenario Base no reconcilia con opportunity.",
    )

    manifest = json.loads(
        (BASE_DIR / prefix / "final" / "pipeline_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    require(manifest.get("pipeline_version") == "2.0.0", "Pipeline sin versión C1.")
    require(manifest.get("mode") == mode, "Modo incorrecto en manifest.")
    require(len(manifest.get("outputs", [])) == 12, "Manifest incompleto.")


def validate_local_links():
    missing = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for document in BASE_DIR.rglob("*.md"):
        for target in link_pattern.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_text = target.split("#", 1)[0]
            resolved = (document.parent / path_text).resolve()
            if not resolved.exists():
                missing.append(f"{document.relative_to(BASE_DIR)} -> {target}")

    require(not missing, "Enlaces locales rotos:\n" + "\n".join(missing))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["full", "demo"], default="full")
    args = parser.parse_args(argv)

    if args.mode == "full":
        validate_readme_metrics()
        validate_notebook()
    else:
        validate_demo_outputs()
    validate_advanced_marts(args.mode)
    validate_privacy(args.mode)
    validate_local_links()
    print(
        f"Validación {args.mode} consistente: "
        "métricas, outputs, privacidad y enlaces verificados."
    )


if __name__ == "__main__":
    main()
