import pandas as pd

from src.business import (
    build_customer_value_summary,
    build_preference_opportunity,
    coverage_signal,
    preference_data_quality,
)


def test_coverage_signal_separates_evidence_from_market_coverage():
    assert preference_data_quality(0.25) == "Baja"
    assert coverage_signal(1.5, 10, "Baja") == "No concluyente"
    assert coverage_signal(1.5, 10, "Alta") == "Brecha de cobertura observada"
    assert coverage_signal(0.5, 10, "Alta") == "Oferta observada amplia"


def test_customer_value_summary_uses_period_spend():
    customers = pd.DataFrame({
        "id_persona": [1, 2],
        "membresia_premium": ["Si", "No"],
        "estrato_socioeconomico": ["Alto", "Bajo"],
        "frecuencia_visita": [4, 2],
        "promedio_gasto_comida": [50.0, 20.0],
        "gasto_periodo_estimado": [200.0, 40.0],
    })

    summary = build_customer_value_summary(customers)
    premium = summary.loc[
        (summary["dimension"] == "Membresia premium")
        & (summary["segment"] == "Si")
    ].iloc[0]

    assert premium["estimated_period_spend"] == 200.0
    assert premium["spend_share"] == 0.8333


def test_preference_opportunity_marks_ambiguous_data_as_not_conclusive():
    customers = pd.DataFrame({
        "preferencias_alimenticias": ["Otro", "Otro", "Vegetariano"],
        "preferencia_original_nula": [True, False, False],
        "gasto_periodo_estimado": [100.0, 80.0, 120.0],
    })
    restaurants = pd.DataFrame({
        "categories": ["Italian", "Vegetarian"],
        "quality_score": [4.2, 4.4],
        "rating": [4.0, 4.5],
        "review_count": [100, 200],
    })
    mapping = pd.DataFrame({
        "customer_preference": ["Otro", "Vegetariano"],
        "yelp_category": ["Italian", "Vegetarian"],
    })

    result = build_preference_opportunity(customers, restaurants, mapping)
    other = result.loc[result["customer_preference"] == "Otro"].iloc[0]

    assert other["preference_data_quality"] == "Baja"
    assert other["coverage_signal"] == "No concluyente"
    assert other["imputed_preference_share"] == 0.5


def test_preference_opportunity_output_is_complete():
    from src.config import CATEGORY_MAPPING, PREFERENCE_OPPORTUNITY_MIAMI

    opportunity = pd.read_csv(PREFERENCE_OPPORTUNITY_MIAMI)
    mapping = pd.read_csv(CATEGORY_MAPPING)

    assert not opportunity.empty
    assert set(opportunity["customer_preference"]) == set(
        mapping["customer_preference"]
    )
    assert (opportunity["demand_coverage_index"].dropna() >= 0).all()
    assert opportunity["observed_restaurant_coverage"].between(0, 1).all()
    assert abs(opportunity["estimated_period_spend_share"].sum() - 1) < 0.001
    assert {
        "preference_data_quality",
        "coverage_signal",
        "recommended_action",
    }.issubset(opportunity.columns)
