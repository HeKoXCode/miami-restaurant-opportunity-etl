from .config import (
    PII_COLUMNS,
    TARGET_CITY,
    VALID_AGE_MAX,
    VALID_AGE_MIN,
    YELP_ALLOWED_CITIES,
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def validate_customers(customers, miami):
    require(not customers["id_persona"].duplicated().any(), "Hay id_persona duplicados.")
    require(
        customers["edad"].between(VALID_AGE_MIN, VALID_AGE_MAX).all(),
        f"Hay edades fuera del rango {VALID_AGE_MIN}-{VALID_AGE_MAX}.",
    )
    require((customers["frecuencia_visita"] >= 0).all(), "Hay frecuencias negativas.")
    require((customers["promedio_gasto_comida"] >= 0).all(), "Hay gastos negativos.")
    require(
        customers["preferencias_alimenticias"].isna().sum() == 0,
        "Quedaron preferencias nulas.",
    )
    require(
        (miami["ciudad_residencia"] == TARGET_CITY).all(),
        f"customers_miami tiene ciudades que no son {TARGET_CITY}.",
    )
    require(
        customers["gasto_periodo_estimado"].equals(
            (customers["frecuencia_visita"] * customers["promedio_gasto_comida"]).round(2)
        ),
        "gasto_periodo_estimado no coincide con frecuencia por gasto.",
    )
    require(
        not set(PII_COLUMNS) & set(customers.columns),
        "El output limpio conserva columnas con PII.",
    )


def validate_yelp(restaurants):
    require(
        not restaurants["restaurant_id"].duplicated().any(),
        "Hay restaurant_id duplicados.",
    )
    require(not restaurants["yelp_id"].duplicated().any(), "Hay yelp_id duplicados.")
    require(restaurants["rating"].between(0, 5).all(), "Hay ratings fuera de 0-5.")
    require((restaurants["review_count"] >= 0).all(), "Hay review_count negativos.")
    require(
        restaurants["city"].isin(YELP_ALLOWED_CITIES).all(),
        "Yelp clean tiene ciudades fuera del recorte.",
    )
    require(restaurants.isna().sum().sum() == 0, "Yelp clean tiene nulos.")
    require(
        restaurants["transactions"].str.contains("pickup, delivery").sum() == 0,
        "Las transacciones no quedaron canonizadas.",
    )


def validate_preference_opportunity(
    preference_opportunity,
    mapping,
):
    require(
        len(preference_opportunity) > 0,
        "preference_opportunity_miami esta vacio.",
    )
    require(
        (preference_opportunity["customer_count"] > 0).all(),
        "Hay preferencias sin clientes.",
    )
    require(
        (preference_opportunity["demand_coverage_index"].dropna() >= 0).all(),
        "Hay indices negativos.",
    )
    require(
        preference_opportunity["observed_restaurant_coverage"].between(0, 1).all(),
        "Hay coberturas de restaurantes fuera de 0-1.",
    )
    require(
        abs(preference_opportunity["customer_share"].sum() - 1) < 0.001,
        "customer_share no suma aproximadamente 1.",
    )
    require(
        abs(preference_opportunity["estimated_period_spend_share"].sum() - 1) < 0.001,
        "estimated_period_spend_share no suma aproximadamente 1.",
    )
    require(
        set(preference_opportunity["customer_preference"])
        == set(mapping["customer_preference"]),
        "El mapping no cubre las mismas preferencias que la tabla de oportunidades.",
    )


def validate_customer_value(customer_value):
    require(not customer_value.empty, "customer_value_miami esta vacio.")
    for _, dimension in customer_value.groupby("dimension"):
        require(
            abs(dimension["customer_share"].sum() - 1) < 0.001,
            "customer_share no suma aproximadamente 1 dentro de una dimension.",
        )
        require(
            abs(dimension["spend_share"].sum() - 1) < 0.001,
            "spend_share no suma aproximadamente 1 dentro de una dimension.",
        )


def validate_rejection_counts(raw, clean, audit, dataset):
    rejected_rows = sum(audit.values())
    require(
        len(raw) - len(clean) == rejected_rows,
        (
            f"Los rechazos de {dataset} no reconcilian: "
            f"raw={len(raw)}, clean={len(clean)}, causas={rejected_rows}."
        ),
    )


def validate_all(
    customers,
    miami,
    restaurants,
    preference_opportunity,
    customer_value,
    mapping,
):
    validate_customers(customers, miami)
    validate_yelp(restaurants)
    validate_preference_opportunity(preference_opportunity, mapping)
    validate_customer_value(customer_value)
