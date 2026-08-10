import pandas as pd

from .config import (
    CUSTOMERS_RAW,
    ESTRATOS,
    PII_COLUMNS,
    PREFERENCE_FILL_VALUE,
    TARGET_CITY,
    VALID_AGE_MAX,
    VALID_AGE_MIN,
)


def load_customers():
    customers = pd.read_csv(CUSTOMERS_RAW, encoding="utf-8-sig")

    for column in ["frecuencia_visita", "promedio_gasto_comida", "edad"]:
        customers[column] = pd.to_numeric(customers[column], errors="coerce")

    return customers


def clean_customers(customers):
    customers = customers.copy()

    customers["frecuencia_imputada"] = False
    customers["gasto_imputado"] = False
    customers["edad_imputada"] = False
    customers["preferencia_original_nula"] = customers["preferencias_alimenticias"].isna()

    negative_frequency_with_spend = (
        (customers["frecuencia_visita"] < 0)
        & (customers["promedio_gasto_comida"] > 0)
    )

    # Si hay gasto pero la frecuencia es negativa, la fila parece útil y el
    # problema está en la frecuencia. Usamos la mediana del mismo estrato.
    for estrato in ESTRATOS:
        mask = negative_frequency_with_spend & (
            customers["estrato_socioeconomico"] == estrato
        )
        median_frequency = customers.loc[
            (customers["estrato_socioeconomico"] == estrato)
            & (customers["frecuencia_visita"] > 0),
            "frecuencia_visita",
        ].median()

        customers.loc[mask, "frecuencia_visita"] = median_frequency
        customers.loc[mask, "frecuencia_imputada"] = True

    missing_spend_with_frequency = (
        customers["promedio_gasto_comida"].isna()
        & (customers["frecuencia_visita"] > 0)
    )

    # Aplicamos la misma idea cuando falta el ticket, pero sí hay visitas.
    for estrato in ESTRATOS:
        mask = missing_spend_with_frequency & (
            customers["estrato_socioeconomico"] == estrato
        )
        median_spend = customers.loc[
            (customers["estrato_socioeconomico"] == estrato)
            & (customers["promedio_gasto_comida"] > 0),
            "promedio_gasto_comida",
        ].median()

        customers.loc[mask, "promedio_gasto_comida"] = median_spend
        customers.loc[mask, "gasto_imputado"] = True

    bad_frequency_without_spend = (
        (customers["frecuencia_visita"] < 0)
        & (customers["promedio_gasto_comida"].isna())
    )
    # Sin frecuencia ni gasto no hay base razonable para imputar consumo.
    customers = customers.loc[~bad_frequency_without_spend].copy()

    missing_frequency_without_spend = (
        customers["frecuencia_visita"].isna()
        & (customers["promedio_gasto_comida"] <= 0)
    )
    customers = customers.loc[~missing_frequency_without_spend].copy()

    # "Otro" ya existía en la fuente. El flag permite distinguir una respuesta
    # real de una preferencia que llegó vacía.
    customers["preferencias_alimenticias"] = customers[
        "preferencias_alimenticias"
    ].fillna(PREFERENCE_FILL_VALUE)

    invalid_age = (
        customers["edad"].isna()
        | (customers["edad"] < VALID_AGE_MIN)
        | (customers["edad"] > VALID_AGE_MAX)
    )
    active_customer = (
        (customers["promedio_gasto_comida"] > 0)
        & (customers["frecuencia_visita"] > 0)
    )

    valid_age = customers["edad"].between(VALID_AGE_MIN, VALID_AGE_MAX)
    average_valid_age = customers.loc[valid_age, "edad"].mean()
    age_to_impute = invalid_age & active_customer
    # Solo recuperamos edades de clientes con actividad; el resto no aporta al análisis.
    customers.loc[age_to_impute, "edad"] = average_valid_age
    customers.loc[age_to_impute, "edad_imputada"] = True

    customers = customers.loc[
        customers["edad"].between(VALID_AGE_MIN, VALID_AGE_MAX)
    ].copy()

    customers["edad"] = customers["edad"].round().astype("Int64")
    customers["frecuencia_visita"] = customers["frecuencia_visita"].round().astype("Int64")
    customers["gasto_periodo_estimado"] = (
        customers["frecuencia_visita"] * customers["promedio_gasto_comida"]
    ).round(2)

    # Los datos de contacto no se usan y no deben salir en archivos analíticos.
    customers = customers.drop(columns=PII_COLUMNS, errors="ignore")

    return customers.reset_index(drop=True)


def build_city_customer_view(customers, city=TARGET_CITY):
    return customers.loc[customers["ciudad_residencia"] == city].copy()
