"""Validate that the published evidence remains consistent with the README."""

from csv import DictReader
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parents[1]


def read_csv(relative_path):
    with (BASE_DIR / relative_path).open(encoding="utf-8-sig", newline="") as file:
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

    require(len(notebook["cells"]) == 22, "El notebook debe conservar 22 celdas.")
    require(len(code_cells) == 8, "El notebook debe conservar 8 celdas de código.")
    require(
        all(cell.get("execution_count") is not None for cell in code_cells),
        "Todas las celdas de código deben quedar ejecutadas.",
    )
    require(
        not any(output.get("output_type") == "error" for output in outputs),
        "El notebook contiene un output de error.",
    )
    require(
        sum("image/png" in output.get("data", {}) for output in outputs) == 4,
        "El notebook debe contener exactamente 4 gráficos PNG.",
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


def validate_privacy():
    forbidden_columns = {"nombre", "apellido", "telefono", "teléfono", "email", "correo"}
    for relative_path in (
        "data/clean/customers_clean.csv",
        "data/final/customers_miami.csv",
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


def main():
    validate_readme_metrics()
    validate_notebook()
    validate_privacy()
    validate_local_links()
    print("Publicación consistente: métricas, notebook, privacidad y enlaces verificados.")


if __name__ == "__main__":
    main()
