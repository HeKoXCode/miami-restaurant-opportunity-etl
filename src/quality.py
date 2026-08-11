import pandas as pd

from .config import SCHEMA_VERSION, VALID_AGE_MAX, VALID_AGE_MIN


def quality_row(dataset, step, df):
    row = {
        "dataset": dataset,
        "step": step,
        "rows": len(df),
        "columns": len(df.columns),
        "missing_total": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    if "id_persona" in df.columns:
        row["duplicate_ids"] = int(df["id_persona"].duplicated().sum())
    if "restaurant_id" in df.columns:
        row["duplicate_ids"] = int(df["restaurant_id"].duplicated().sum())
    if "yelp_id" in df.columns:
        row["duplicate_yelp_ids"] = int(df["yelp_id"].duplicated().sum())
    if "frecuencia_visita" in df.columns:
        row["negative_frequency"] = int((df["frecuencia_visita"] < 0).sum())
    if "promedio_gasto_comida" in df.columns:
        row["missing_spend"] = int(df["promedio_gasto_comida"].isna().sum())
    if "edad" in df.columns:
        row["invalid_age"] = int(
            (
                df["edad"].isna()
                | (df["edad"] < VALID_AGE_MIN)
                | (df["edad"] > VALID_AGE_MAX)
            ).sum()
        )
    if "rating" in df.columns:
        rating = pd.to_numeric(df["rating"], errors="coerce")
        row["rating_outside_0_5"] = int((~rating.between(0, 5)).sum())

    return row


def build_data_quality_report(rows):
    report = pd.DataFrame(rows)
    preferred_order = [
        "dataset",
        "step",
        "rows",
        "columns",
        "missing_total",
        "duplicate_rows",
        "duplicate_ids",
        "duplicate_yelp_ids",
        "negative_frequency",
        "missing_spend",
        "invalid_age",
        "rating_outside_0_5",
    ]
    columns = [column for column in preferred_order if column in report.columns]
    columns += [column for column in report.columns if column not in columns]
    return report[columns]


def build_rejection_report(customer_audit, yelp_audit):
    rows = []
    for dataset, audit in (
        ("customers", customer_audit),
        ("yelp", yelp_audit),
    ):
        rows.extend(
            {
                "dataset": dataset,
                "step": "clean",
                "reason": reason,
                "rows_rejected": count,
            }
            for reason, count in audit.items()
        )
    return pd.DataFrame(rows).sort_values(
        ["dataset", "reason"],
    ).reset_index(drop=True)


def _markdown_table(df):
    safe = df.fillna("")
    headers = list(safe.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in safe.iterrows():
        values = [str(row[column]) for column in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def data_quality_to_markdown(report, rejections, mode):
    customers_clean = report.loc[
        (report["dataset"] == "customers") & (report["step"] == "clean")
    ]
    yelp_clean = report.loc[
        (report["dataset"] == "yelp") & (report["step"] == "clean")
    ]

    notes = []
    if not customers_clean.empty:
        notes.append(
            f"- Clientes limpios: {int(customers_clean.iloc[0]['rows']):,} filas."
        )
    if not yelp_clean.empty:
        notes.append(
            f"- Restaurantes Yelp limpios: {int(yelp_clean.iloc[0]['rows']):,} filas."
        )

    notes_text = "\n".join(notes)
    return (
        "# Reporte de calidad\n\n"
        "Control operativo generado por el pipeline. Resume el volumen de cada etapa "
        "y los problemas de calidad que deben quedar resueltos antes del analisis.\n\n"
        f"- Modo: `{mode}`.\n"
        f"- Versión de contratos: `{SCHEMA_VERSION}`.\n"
        f"{notes_text}\n\n"
        + _markdown_table(report)
        + "\n\n## Filas rechazadas\n\n"
        + "Los conteos explican la diferencia entre raw y clean por causa.\n\n"
        + _markdown_table(rejections)
        + "\n"
    )


def save_data_quality_reports(
    report: pd.DataFrame,
    rejections: pd.DataFrame,
    csv_path,
    rejections_path,
    markdown_path,
    mode,
) -> None:
    report.to_csv(csv_path, index=False, encoding="utf-8")
    rejections.to_csv(rejections_path, index=False, encoding="utf-8")
    markdown_path.write_text(
        data_quality_to_markdown(report, rejections, mode),
        encoding="utf-8",
    )
