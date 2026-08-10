import pandas as pd

from src.config import (
    CUSTOMER_VALUE_MIAMI,
    CUSTOMERS_CLEAN,
    CUSTOMERS_MIAMI,
    DATA_QUALITY_REPORT_CSV,
    DATA_QUALITY_REPORT_MD,
    PII_COLUMNS,
    PREFERENCE_FILL_VALUE,
    TARGET_CITY,
    VALID_AGE_MAX,
    VALID_AGE_MIN,
)


def test_customers_have_valid_core_fields():
    customers = pd.read_csv(CUSTOMERS_CLEAN)

    assert customers["id_persona"].is_unique
    assert customers["edad"].between(VALID_AGE_MIN, VALID_AGE_MAX).all()
    assert (customers["frecuencia_visita"] >= 0).all()
    assert (customers["promedio_gasto_comida"] >= 0).all()
    assert customers["preferencias_alimenticias"].isna().sum() == 0
    assert PREFERENCE_FILL_VALUE in set(customers["preferencias_alimenticias"])


def test_miami_file_only_has_miami_customers():
    miami = pd.read_csv(CUSTOMERS_MIAMI)

    assert not miami.empty
    assert set(miami["ciudad_residencia"].unique()) == {TARGET_CITY}


def test_period_spend_is_reproducible():
    customers = pd.read_csv(CUSTOMERS_CLEAN)
    expected = (
        customers["frecuencia_visita"] * customers["promedio_gasto_comida"]
    ).round(2)

    assert customers["gasto_periodo_estimado"].equals(expected)


def test_public_customer_outputs_do_not_include_pii():
    customers = pd.read_csv(CUSTOMERS_CLEAN)
    miami = pd.read_csv(CUSTOMERS_MIAMI)

    assert not set(PII_COLUMNS) & set(customers.columns)
    assert not set(PII_COLUMNS) & set(miami.columns)


def test_customer_value_summary_balances_each_dimension():
    summary = pd.read_csv(CUSTOMER_VALUE_MIAMI)

    assert not summary.empty
    for _, dimension in summary.groupby("dimension"):
        assert abs(dimension["customer_share"].sum() - 1) < 0.001
        assert abs(dimension["spend_share"].sum() - 1) < 0.001


def test_quality_report_tracks_customer_steps():
    report = pd.read_csv(DATA_QUALITY_REPORT_CSV)
    customer_steps = set(report.loc[report["dataset"] == "customers", "step"])

    assert {"raw", "clean", "final_miami"}.issubset(customer_steps)
    assert "customer_value" in set(report["dataset"])
    assert DATA_QUALITY_REPORT_MD.exists()
