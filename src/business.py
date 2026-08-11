import pandas as pd

from .config import (
    CATEGORY_MAPPING,
    COVERAGE_GAP_THRESHOLD,
    COVERAGE_WIDE_THRESHOLD,
    PREFERENCE_LOW_CONFIDENCE_THRESHOLD,
    PREFERENCE_MEDIUM_CONFIDENCE_THRESHOLD,
    TARGET_CITY,
)


def load_category_mapping(path=CATEGORY_MAPPING):
    mapping = pd.read_csv(path, encoding="utf-8")
    required_columns = {"customer_preference", "yelp_category"}
    missing_columns = required_columns - set(mapping.columns)

    if missing_columns:
        raise ValueError(f"Faltan columnas en category_mapping.csv: {missing_columns}")

    return mapping


def mapping_as_dict(mapping):
    """Agrupa las categorías de Yelp que representan cada preferencia."""
    return (
        mapping.groupby("customer_preference")["yelp_category"]
        .apply(lambda values: sorted(set(values)))
        .to_dict()
    )


def restaurants_for_preference(restaurants, expected_categories):
    expected_categories = set(expected_categories)

    def matches_preference(category_text):
        restaurant_categories = {
            category.strip()
            for category in str(category_text).split(",")
            if category.strip()
        }
        return bool(restaurant_categories & expected_categories)

    # Un restaurante puede cubrir más de una preferencia. Es intencional:
    # hablamos de cobertura observable, no de categorías exclusivas.
    matches = restaurants["categories"].apply(matches_preference)
    return restaurants.loc[matches].copy()


def preference_data_quality(imputed_share):
    if imputed_share >= PREFERENCE_LOW_CONFIDENCE_THRESHOLD:
        return "Baja"
    if imputed_share >= PREFERENCE_MEDIUM_CONFIDENCE_THRESHOLD:
        return "Media"
    return "Alta"


def coverage_signal(
    index_value,
    restaurant_count,
    data_quality,
    gap_threshold=COVERAGE_GAP_THRESHOLD,
    wide_threshold=COVERAGE_WIDE_THRESHOLD,
):
    # Una preferencia con demasiados datos imputados no debería terminar
    # etiquetada como oportunidad, aunque el índice parezca atractivo.
    if data_quality == "Baja":
        return "No concluyente"
    if restaurant_count == 0:
        return "Sin oferta observada"
    if index_value >= gap_threshold:
        return "Brecha de cobertura observada"
    if index_value <= wide_threshold:
        return "Oferta observada amplia"
    return "Cobertura observada equilibrada"


def recommended_action(signal):
    actions = {
        "No concluyente": "Reclasificar preferencias antes de decidir",
        "Sin oferta observada": "Validar demanda y buscar oferta fuera de la muestra",
        "Brecha de cobertura observada": (
            "Validar concepto, ubicacion y disposicion a pagar"
        ),
        "Oferta observada amplia": (
            "Competir por diferenciacion, no por volumen de oferta"
        ),
        "Cobertura observada equilibrada": (
            "Evaluar nichos, ticket y ubicacion antes de expandir"
        ),
    }
    return actions[signal]


def summarize_customer_dimension(customers, column, dimension_name):
    summary = (
        customers.groupby(column, as_index=False, dropna=False)
        .agg(
            customer_count=("id_persona", "count"),
            avg_visit_frequency=("frecuencia_visita", "mean"),
            avg_ticket=("promedio_gasto_comida", "mean"),
            avg_estimated_period_spend=("gasto_periodo_estimado", "mean"),
            estimated_period_spend=("gasto_periodo_estimado", "sum"),
        )
        .rename(columns={column: "segment"})
    )
    summary.insert(0, "dimension", dimension_name)
    return summary


def build_customer_value_summary(customers):
    # Se muestran dos lecturas simples del mismo cliente: membresía y estrato.
    # Las dejamos juntas en una tabla para que el notebook no repita cálculos.
    premium = summarize_customer_dimension(
        customers,
        "membresia_premium",
        "Membresia premium",
    )
    socioeconomic = summarize_customer_dimension(
        customers,
        "estrato_socioeconomico",
        "Estrato socioeconomico",
    )
    result = pd.concat([premium, socioeconomic], ignore_index=True)

    total_customers = len(customers)
    total_spend = customers["gasto_periodo_estimado"].sum()
    result["customer_share"] = result["customer_count"] / total_customers
    result["spend_share"] = result["estimated_period_spend"] / total_spend

    columns_to_round = [
        "avg_visit_frequency",
        "avg_ticket",
        "avg_estimated_period_spend",
        "estimated_period_spend",
    ]
    result[columns_to_round] = result[columns_to_round].round(2)
    result[["customer_share", "spend_share"]] = result[
        ["customer_share", "spend_share"]
    ].round(4)

    return result.sort_values(
        ["dimension", "estimated_period_spend"],
        ascending=[True, False],
    ).reset_index(drop=True)


def build_preference_opportunity(
    customers,
    restaurants,
    mapping,
    city=TARGET_CITY,
):
    preference_to_yelp = mapping_as_dict(mapping)
    total_customers = len(customers)
    total_restaurants = len(restaurants)
    total_spend = customers["gasto_periodo_estimado"].sum()

    rows = []

    for preference, yelp_categories in preference_to_yelp.items():
        preference_customers = customers.loc[
            customers["preferencias_alimenticias"] == preference
        ]
        matching_restaurants = restaurants_for_preference(
            restaurants,
            yelp_categories,
        )

        customer_count = len(preference_customers)
        restaurant_count = len(matching_restaurants)
        customer_share = customer_count / total_customers
        observed_coverage = restaurant_count / total_restaurants

        if observed_coverage == 0:
            coverage_index = None
        else:
            coverage_index = customer_share / observed_coverage

        imputed_count = int(
            preference_customers["preferencia_original_nula"].sum()
        )
        imputed_share = imputed_count / customer_count
        data_quality = preference_data_quality(imputed_share)
        signal = coverage_signal(coverage_index, restaurant_count, data_quality)
        estimated_spend = preference_customers["gasto_periodo_estimado"].sum()

        # Guardamos las piezas por separado. Así quien lee la tabla puede ver
        # por qué aparece una recomendación y no tiene que confiar en un score oculto.
        rows.append({
            "city": city,
            "customer_preference": preference,
            "mapped_yelp_categories": ", ".join(yelp_categories),
            "customer_count": customer_count,
            "customer_share": round(customer_share, 4),
            "imputed_preference_count": imputed_count,
            "imputed_preference_share": round(imputed_share, 4),
            "preference_data_quality": data_quality,
            "avg_estimated_period_spend": round(
                preference_customers["gasto_periodo_estimado"].mean(),
                2,
            ),
            "estimated_period_spend": round(estimated_spend, 2),
            "estimated_period_spend_share": round(
                estimated_spend / total_spend,
                4,
            ),
            "restaurant_count": restaurant_count,
            "observed_restaurant_coverage": round(observed_coverage, 4),
            "avg_rating": round(matching_restaurants["rating"].mean(), 2)
            if restaurant_count
            else 0,
            "median_review_count": round(
                matching_restaurants["review_count"].median(),
                0,
            )
            if restaurant_count
            else 0,
            "avg_quality_score": round(
                matching_restaurants["quality_score"].mean(),
                2,
            )
            if restaurant_count
            else 0,
            "demand_coverage_index": round(coverage_index, 2)
            if coverage_index is not None
            else pd.NA,
            "coverage_signal": signal,
            "recommended_action": recommended_action(signal),
        })

    result = pd.DataFrame(rows)
    return result.sort_values(
        ["preference_data_quality", "demand_coverage_index"],
        ascending=[True, False],
    ).reset_index(drop=True)


PRICE_SEGMENTS = {
    0: "Sin precio",
    1: "$",
    2: "$$",
    3: "$$$",
    4: "$$$$",
}


def build_restaurant_competition(
    restaurants,
    mapping,
    city=TARGET_CITY,
):
    """Compare observable restaurant supply by preference and Yelp price band."""
    preference_to_yelp = mapping_as_dict(mapping)
    rows = []
    for preference, yelp_categories in preference_to_yelp.items():
        matching = restaurants_for_preference(restaurants, yelp_categories)
        total_matching = len(matching)
        for price_level, price_segment in PRICE_SEGMENTS.items():
            price_slice = matching.loc[matching["price_level"] == price_level]
            restaurant_count = len(price_slice)
            rows.append({
                "city": city,
                "customer_preference": preference,
                "price_level": price_level,
                "price_segment": price_segment,
                "restaurant_count": restaurant_count,
                "restaurant_share_within_preference": round(
                    restaurant_count / total_matching if total_matching else 0,
                    4,
                ),
                "imputed_price_count": int(price_slice["price_was_missing"].sum()),
                "imputed_price_share": round(
                    price_slice["price_was_missing"].mean(),
                    4,
                )
                if restaurant_count
                else 0,
                "avg_rating": round(price_slice["rating"].mean(), 2)
                if restaurant_count
                else 0,
                "median_review_count": round(price_slice["review_count"].median(), 0)
                if restaurant_count
                else 0,
                "avg_quality_score": round(price_slice["quality_score"].mean(), 2)
                if restaurant_count
                else 0,
                "delivery_share": round(price_slice["has_delivery"].mean(), 4)
                if restaurant_count
                else 0,
                "reservation_share": round(
                    price_slice["has_reservation"].mean(),
                    4,
                )
                if restaurant_count
                else 0,
            })
    return pd.DataFrame(rows).sort_values(
        ["customer_preference", "price_level"]
    ).reset_index(drop=True)


SENSITIVITY_SCENARIOS = (
    ("Conservador", 1.50, 0.60),
    ("Base", COVERAGE_GAP_THRESHOLD, COVERAGE_WIDE_THRESHOLD),
    ("Exploratorio", 1.10, 0.90),
)


def build_preference_sensitivity(preference_opportunity):
    """Expose how opportunity labels respond to plausible threshold choices."""
    rows = []
    for opportunity in preference_opportunity.to_dict(orient="records"):
        for scenario, gap_threshold, wide_threshold in SENSITIVITY_SCENARIOS:
            signal = coverage_signal(
                opportunity["demand_coverage_index"],
                opportunity["restaurant_count"],
                opportunity["preference_data_quality"],
                gap_threshold=gap_threshold,
                wide_threshold=wide_threshold,
            )
            rows.append({
                "city": opportunity["city"],
                "customer_preference": opportunity["customer_preference"],
                "scenario": scenario,
                "gap_threshold": gap_threshold,
                "wide_threshold": wide_threshold,
                "demand_coverage_index": opportunity["demand_coverage_index"],
                "preference_data_quality": opportunity[
                    "preference_data_quality"
                ],
                "restaurant_count": opportunity["restaurant_count"],
                "coverage_signal": signal,
            })

    result = pd.DataFrame(rows)
    signal_counts = result.groupby("customer_preference")["coverage_signal"].transform(
        "nunique"
    )
    result["stable_across_scenarios"] = signal_counts.eq(1)
    scenario_order = {name: index for index, (name, _, _) in enumerate(SENSITIVITY_SCENARIOS)}
    result["_scenario_order"] = result["scenario"].map(scenario_order)
    return result.sort_values(
        ["customer_preference", "_scenario_order"]
    ).drop(columns="_scenario_order").reset_index(drop=True)
