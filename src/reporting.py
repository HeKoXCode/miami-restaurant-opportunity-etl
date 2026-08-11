"""Reusable report preparation built only from final pipeline outputs."""

from dataclasses import dataclass

import pandas as pd

from .config import FULL_PIPELINE_PATHS, PipelinePaths


@dataclass(frozen=True)
class ReportData:
    customers_miami: pd.DataFrame
    customer_value: pd.DataFrame
    preference_opportunity: pd.DataFrame
    restaurant_competition: pd.DataFrame
    preference_sensitivity: pd.DataFrame
    data_quality: pd.DataFrame


def load_report_data(paths: PipelinePaths = FULL_PIPELINE_PATHS) -> ReportData:
    """Load only machine-readable final outputs; never raw or clean sources."""
    return ReportData(
        customers_miami=pd.read_csv(paths.customers_miami),
        customer_value=pd.read_csv(paths.customer_value_miami),
        preference_opportunity=pd.read_csv(paths.preference_opportunity_miami),
        restaurant_competition=pd.read_csv(paths.restaurant_competition_miami),
        preference_sensitivity=pd.read_csv(paths.preference_sensitivity_miami),
        data_quality=pd.read_csv(paths.data_quality_report_csv),
    )


def _single_row(dataframe, **filters):
    matches = dataframe.copy()
    for column, value in filters.items():
        matches = matches.loc[matches[column] == value]
    if len(matches) != 1:
        criteria = ", ".join(f"{key}={value}" for key, value in filters.items())
        raise ValueError(f"Se esperaba una fila para {criteria}; se encontraron {len(matches)}.")
    return matches.iloc[0]


def build_executive_metrics(report: ReportData) -> dict:
    premium = _single_row(
        report.customer_value,
        dimension="Membresia premium",
        segment="Sí",
    )
    high_value = _single_row(
        report.customer_value,
        dimension="Estrato socioeconomico",
        segment="Muy Alto",
    )
    vegetarian = _single_row(
        report.preference_opportunity,
        customer_preference="Vegetariano",
    )
    seafood = _single_row(
        report.preference_opportunity,
        customer_preference="Mariscos",
    )
    return {
        "customer_count": len(report.customers_miami),
        "estimated_period_spend": report.customers_miami[
            "gasto_periodo_estimado"
        ].sum(),
        "premium_customer_share": premium["customer_share"],
        "premium_spend_share": premium["spend_share"],
        "high_value_customer_share": high_value["customer_share"],
        "high_value_spend_share": high_value["spend_share"],
        "vegetarian_coverage_index": vegetarian["demand_coverage_index"],
        "seafood_estimated_spend": seafood["estimated_period_spend"],
    }


def build_premium_view(customer_value):
    return (
        customer_value.loc[customer_value["dimension"] == "Membresia premium"]
        .set_index("segment")[["customer_share", "spend_share"]]
        .rename(
            columns={
                "customer_share": "Participación de clientes",
                "spend_share": "Participación del gasto",
            }
        )
    )


def build_stratum_view(customer_value):
    return customer_value.loc[
        customer_value["dimension"] == "Estrato socioeconomico"
    ].sort_values("estimated_period_spend")


def build_preference_value_view(preference_opportunity):
    return preference_opportunity.sort_values(
        "estimated_period_spend",
        ascending=True,
    ).copy()


def build_priority_view(preference_opportunity):
    return preference_opportunity.loc[
        preference_opportunity["preference_data_quality"] != "Baja",
        [
            "customer_preference",
            "customer_count",
            "estimated_period_spend",
            "demand_coverage_index",
            "coverage_signal",
            "recommended_action",
        ],
    ].sort_values(
        ["coverage_signal", "estimated_period_spend"],
        ascending=[True, False],
    )


def build_quality_view(data_quality):
    return data_quality[
        ["dataset", "step", "rows", "columns", "missing_total", "duplicate_rows"]
    ].copy()


def build_price_competition_view(restaurant_competition):
    return restaurant_competition.pivot(
        index="customer_preference",
        columns="price_level",
        values="restaurant_count",
    ).reindex(columns=[0, 1, 2, 3, 4]).rename(
        columns={
            0: "Sin precio",
            1: "Nivel 1",
            2: "Nivel 2",
            3: "Nivel 3",
            4: "Nivel 4",
        }
    )


def build_sensitivity_view(preference_sensitivity):
    return preference_sensitivity.pivot(
        index="customer_preference",
        columns="scenario",
        values="coverage_signal",
    ).reindex(columns=["Conservador", "Base", "Exploratorio"])
