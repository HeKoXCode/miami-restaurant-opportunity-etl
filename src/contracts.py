"""Versioned dataframe contracts for pipeline inputs and outputs."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import (
    CUSTOMER_PREFERENCES,
    ESTRATOS,
    PII_COLUMNS,
    SCHEMA_VERSION,
    TARGET_CITY,
    VALID_AGE_MAX,
    VALID_AGE_MIN,
    YELP_ALLOWED_CITIES,
)


class DataContractError(ValueError):
    """Raised when a dataframe does not match its declared contract."""


@dataclass(frozen=True)
class ColumnRule:
    kind: str = "any"
    nullable: bool = True
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: frozenset | None = None


@dataclass(frozen=True)
class DataContract:
    name: str
    columns: dict[str, ColumnRule]
    version: str = SCHEMA_VERSION
    allow_extra_columns: bool = False
    unique_keys: tuple[tuple[str, ...], ...] = ()
    forbidden_columns: frozenset[str] = field(default_factory=frozenset)
    required_values: dict[str, frozenset] = field(default_factory=dict)
    min_rows: int = 1


def _validate_kind(series: pd.Series, rule: ColumnRule) -> list[str]:
    errors = []
    observed = series.dropna()
    if rule.kind in {"numeric", "integer"}:
        numeric = pd.to_numeric(observed, errors="coerce")
        invalid_count = int(numeric.isna().sum())
        if invalid_count:
            errors.append(f"{invalid_count} valores no son {rule.kind}")
            return errors
        if rule.kind == "integer":
            non_integer = int(((numeric % 1).abs() > 1e-9).sum())
            if non_integer:
                errors.append(f"{non_integer} valores no son enteros")
        if rule.minimum is not None:
            below = int((numeric < rule.minimum).sum())
            if below:
                errors.append(f"{below} valores son menores que {rule.minimum}")
        if rule.maximum is not None:
            above = int((numeric > rule.maximum).sum())
            if above:
                errors.append(f"{above} valores son mayores que {rule.maximum}")
    elif rule.kind == "string":
        invalid_count = int((~observed.map(lambda value: isinstance(value, str))).sum())
        if invalid_count:
            errors.append(f"{invalid_count} valores no son texto")
    elif rule.kind == "boolean":
        invalid_count = int(
            (~observed.map(lambda value: isinstance(value, (bool, np.bool_)))).sum()
        )
        if invalid_count:
            errors.append(f"{invalid_count} valores no son booleanos")
    elif rule.kind == "identifier":
        invalid_count = int(
            (
                ~observed.map(
                    lambda value: isinstance(value, (str, int, float, np.number))
                    and not isinstance(value, (bool, np.bool_))
                )
            ).sum()
        )
        if invalid_count:
            errors.append(f"{invalid_count} valores no son identificadores")
    return errors


def validate_contract(
    dataframe: pd.DataFrame,
    contract: DataContract,
    stage: str,
) -> None:
    errors = []
    actual_columns = set(dataframe.columns)
    expected_columns = set(contract.columns)
    missing = sorted(expected_columns - actual_columns)
    extra = sorted(actual_columns - expected_columns)
    forbidden = sorted(actual_columns & set(contract.forbidden_columns))

    if missing:
        errors.append(f"faltan columnas: {', '.join(missing)}")
    if extra and not contract.allow_extra_columns:
        errors.append(f"sobran columnas: {', '.join(extra)}")
    if forbidden:
        errors.append(f"columnas prohibidas: {', '.join(forbidden)}")
    if len(dataframe) < contract.min_rows:
        errors.append(
            f"se esperaban al menos {contract.min_rows} filas y llegaron {len(dataframe)}"
        )

    for column, rule in contract.columns.items():
        if column not in dataframe:
            continue
        series = dataframe[column]
        if not rule.nullable:
            null_count = int(series.isna().sum())
            if null_count:
                errors.append(f"{column}: {null_count} nulos no permitidos")
        for issue in _validate_kind(series, rule):
            errors.append(f"{column}: {issue}")
        if rule.allowed_values is not None:
            unexpected = sorted(
                set(series.dropna().unique()) - set(rule.allowed_values),
                key=str,
            )
            if unexpected:
                errors.append(f"{column}: valores no permitidos {unexpected}")

    for key in contract.unique_keys:
        if all(column in dataframe for column in key):
            duplicate_count = int(dataframe.duplicated(subset=list(key)).sum())
            if duplicate_count:
                errors.append(
                    f"clave {', '.join(key)}: {duplicate_count} duplicados"
                )

    for column, required in contract.required_values.items():
        if column in dataframe:
            missing_values = sorted(required - set(dataframe[column].dropna()), key=str)
            if missing_values:
                errors.append(f"{column}: faltan valores requeridos {missing_values}")

    if errors:
        details = "; ".join(errors)
        raise DataContractError(
            f"Contrato {contract.name} v{contract.version} inválido en {stage}: {details}."
        )


RAW_CUSTOMER_COLUMNS = [
    "id_persona",
    "nombre",
    "apellido",
    "edad",
    "genero",
    "ciudad_residencia",
    "estrato_socioeconomico",
    "frecuencia_visita",
    "promedio_gasto_comida",
    "ocio",
    "consume_licor",
    "preferencias_alimenticias",
    "membresia_premium",
    "telefono_contacto",
    "correo_electronico",
    "tipo_de_pago_mas_usado",
    "ingresos_mensuales",
]

CLEAN_CUSTOMER_COLUMNS = [
    "id_persona",
    "edad",
    "genero",
    "ciudad_residencia",
    "estrato_socioeconomico",
    "frecuencia_visita",
    "promedio_gasto_comida",
    "ocio",
    "consume_licor",
    "preferencias_alimenticias",
    "membresia_premium",
    "tipo_de_pago_mas_usado",
    "ingresos_mensuales",
    "frecuencia_imputada",
    "gasto_imputado",
    "edad_imputada",
    "preferencia_original_nula",
    "gasto_periodo_estimado",
]

YELP_CLEAN_COLUMNS = [
    "restaurant_id",
    "yelp_id",
    "name",
    "rating",
    "review_count",
    "quality_score",
    "price",
    "price_level",
    "price_was_missing",
    "phone",
    "has_phone",
    "categories",
    "main_category",
    "category_count",
    "transactions",
    "has_delivery",
    "has_pickup",
    "has_reservation",
    "latitude",
    "longitude",
    "address",
    "city",
    "state",
    "zip_code",
    "country",
]

CUSTOMER_VALUE_COLUMNS = [
    "dimension",
    "segment",
    "customer_count",
    "avg_visit_frequency",
    "avg_ticket",
    "avg_estimated_period_spend",
    "estimated_period_spend",
    "customer_share",
    "spend_share",
]

PREFERENCE_OPPORTUNITY_COLUMNS = [
    "city",
    "customer_preference",
    "mapped_yelp_categories",
    "customer_count",
    "customer_share",
    "imputed_preference_count",
    "imputed_preference_share",
    "preference_data_quality",
    "avg_estimated_period_spend",
    "estimated_period_spend",
    "estimated_period_spend_share",
    "restaurant_count",
    "observed_restaurant_coverage",
    "avg_rating",
    "median_review_count",
    "avg_quality_score",
    "demand_coverage_index",
    "coverage_signal",
    "recommended_action",
]


def _rules(columns: list[str], nullable: bool = False) -> dict[str, ColumnRule]:
    return {column: ColumnRule(nullable=nullable) for column in columns}


raw_customer_rules = _rules(RAW_CUSTOMER_COLUMNS, nullable=True)
for column in (
    "nombre",
    "apellido",
    "genero",
    "ciudad_residencia",
    "ocio",
    "consume_licor",
    "membresia_premium",
    "telefono_contacto",
    "correo_electronico",
    "tipo_de_pago_mas_usado",
):
    raw_customer_rules[column] = ColumnRule("string")
raw_customer_rules.update(
    {
        "id_persona": ColumnRule("integer", nullable=False),
        "edad": ColumnRule("numeric"),
        "estrato_socioeconomico": ColumnRule(
            "string", allowed_values=frozenset(ESTRATOS)
        ),
        "frecuencia_visita": ColumnRule("numeric"),
        "promedio_gasto_comida": ColumnRule("numeric"),
        "preferencias_alimenticias": ColumnRule(
            "string", allowed_values=frozenset(CUSTOMER_PREFERENCES)
        ),
        "ingresos_mensuales": ColumnRule("numeric"),
    }
)
CUSTOMERS_RAW_CONTRACT = DataContract(
    "customers_raw",
    raw_customer_rules,
    unique_keys=(("id_persona",),),
)

yelp_raw_columns = [
    "id",
    "alias",
    "name",
    "image_url",
    "is_closed",
    "review_count",
    "categories",
    "rating",
    "coordinates",
    "transactions",
    "price",
    "location",
    "phone",
    "display_phone",
    "distance",
]
yelp_raw_rules = _rules(yelp_raw_columns, nullable=True)
for column in (
    "alias",
    "image_url",
    "categories",
    "coordinates",
    "transactions",
    "price",
    "location",
    "display_phone",
):
    yelp_raw_rules[column] = ColumnRule("string")
yelp_raw_rules.update(
    {
        "id": ColumnRule("string", nullable=False),
        "name": ColumnRule("string", nullable=False),
        "is_closed": ColumnRule("boolean"),
        "rating": ColumnRule("numeric"),
        "review_count": ColumnRule("numeric"),
        "phone": ColumnRule("numeric"),
        "distance": ColumnRule("numeric"),
    }
)
YELP_RAW_CONTRACT = DataContract(
    "yelp_raw",
    yelp_raw_rules,
    allow_extra_columns=True,
)

CATEGORY_MAPPING_CONTRACT = DataContract(
    "category_mapping",
    {
        "customer_preference": ColumnRule(
            "string",
            nullable=False,
            allowed_values=frozenset(CUSTOMER_PREFERENCES),
        ),
        "yelp_category": ColumnRule("string", nullable=False),
    },
    unique_keys=(("customer_preference", "yelp_category"),),
    required_values={"customer_preference": frozenset(CUSTOMER_PREFERENCES)},
)

clean_customer_rules = _rules(CLEAN_CUSTOMER_COLUMNS)
for column in (
    "genero",
    "ciudad_residencia",
    "ocio",
    "consume_licor",
    "membresia_premium",
    "tipo_de_pago_mas_usado",
):
    clean_customer_rules[column] = ColumnRule("string", nullable=False)
clean_customer_rules.update(
    {
        "id_persona": ColumnRule("integer", nullable=False),
        "edad": ColumnRule(
            "integer", nullable=False, minimum=VALID_AGE_MIN, maximum=VALID_AGE_MAX
        ),
        "estrato_socioeconomico": ColumnRule(
            "string", nullable=False, allowed_values=frozenset(ESTRATOS)
        ),
        "frecuencia_visita": ColumnRule("integer", nullable=False, minimum=0),
        "promedio_gasto_comida": ColumnRule("numeric", nullable=False, minimum=0),
        "preferencias_alimenticias": ColumnRule(
            "string",
            nullable=False,
            allowed_values=frozenset(CUSTOMER_PREFERENCES),
        ),
        "ingresos_mensuales": ColumnRule("numeric", nullable=False, minimum=0),
        "frecuencia_imputada": ColumnRule("boolean", nullable=False),
        "gasto_imputado": ColumnRule("boolean", nullable=False),
        "edad_imputada": ColumnRule("boolean", nullable=False),
        "preferencia_original_nula": ColumnRule("boolean", nullable=False),
        "gasto_periodo_estimado": ColumnRule("numeric", nullable=False, minimum=0),
    }
)
CUSTOMERS_CLEAN_CONTRACT = DataContract(
    "customers_clean",
    clean_customer_rules,
    unique_keys=(("id_persona",),),
    forbidden_columns=frozenset(PII_COLUMNS),
)

miami_rules = dict(clean_customer_rules)
miami_rules["ciudad_residencia"] = ColumnRule(
    "string", nullable=False, allowed_values=frozenset({TARGET_CITY})
)
CUSTOMERS_MIAMI_CONTRACT = DataContract(
    "customers_miami",
    miami_rules,
    unique_keys=(("id_persona",),),
    forbidden_columns=frozenset(PII_COLUMNS),
)

yelp_clean_rules = _rules(YELP_CLEAN_COLUMNS)
for column in (
    "yelp_id",
    "name",
    "price",
    "phone",
    "categories",
    "main_category",
    "transactions",
    "address",
    "city",
    "state",
    "country",
):
    yelp_clean_rules[column] = ColumnRule("string", nullable=False)
yelp_clean_rules["zip_code"] = ColumnRule("identifier", nullable=False)
yelp_clean_rules.update(
    {
        "restaurant_id": ColumnRule("integer", nullable=False, minimum=1),
        "yelp_id": ColumnRule("string", nullable=False),
        "rating": ColumnRule("numeric", nullable=False, minimum=0, maximum=5),
        "review_count": ColumnRule("integer", nullable=False, minimum=0),
        "quality_score": ColumnRule("numeric", nullable=False, minimum=0, maximum=5),
        "price_level": ColumnRule("integer", nullable=False, minimum=0, maximum=4),
        "price_was_missing": ColumnRule("boolean", nullable=False),
        "has_phone": ColumnRule("boolean", nullable=False),
        "category_count": ColumnRule("integer", nullable=False, minimum=0),
        "has_delivery": ColumnRule("boolean", nullable=False),
        "has_pickup": ColumnRule("boolean", nullable=False),
        "has_reservation": ColumnRule("boolean", nullable=False),
        "latitude": ColumnRule("numeric", nullable=False, minimum=-90, maximum=90),
        "longitude": ColumnRule("numeric", nullable=False, minimum=-180, maximum=180),
        "city": ColumnRule(
            "string", nullable=False, allowed_values=frozenset(YELP_ALLOWED_CITIES)
        ),
    }
)
YELP_CLEAN_CONTRACT = DataContract(
    "yelp_clean",
    yelp_clean_rules,
    unique_keys=(("restaurant_id",), ("yelp_id",)),
)

customer_value_rules = _rules(CUSTOMER_VALUE_COLUMNS)
customer_value_rules.update(
    {
        "dimension": ColumnRule("string", nullable=False),
        "segment": ColumnRule("string", nullable=False),
        "customer_count": ColumnRule("integer", nullable=False, minimum=1),
        "avg_visit_frequency": ColumnRule("numeric", nullable=False, minimum=0),
        "avg_ticket": ColumnRule("numeric", nullable=False, minimum=0),
        "avg_estimated_period_spend": ColumnRule(
            "numeric", nullable=False, minimum=0
        ),
        "estimated_period_spend": ColumnRule("numeric", nullable=False, minimum=0),
        "customer_share": ColumnRule("numeric", nullable=False, minimum=0, maximum=1),
        "spend_share": ColumnRule("numeric", nullable=False, minimum=0, maximum=1),
    }
)
CUSTOMER_VALUE_CONTRACT = DataContract("customer_value", customer_value_rules)

opportunity_rules = _rules(PREFERENCE_OPPORTUNITY_COLUMNS)
for column in (
    "mapped_yelp_categories",
    "preference_data_quality",
    "coverage_signal",
    "recommended_action",
):
    opportunity_rules[column] = ColumnRule("string", nullable=False)
for column in (
    "customer_count",
    "imputed_preference_count",
    "restaurant_count",
):
    opportunity_rules[column] = ColumnRule("integer", nullable=False, minimum=0)
for column in (
    "customer_share",
    "imputed_preference_share",
    "estimated_period_spend_share",
    "observed_restaurant_coverage",
):
    opportunity_rules[column] = ColumnRule(
        "numeric", nullable=False, minimum=0, maximum=1
    )
for column in (
    "avg_estimated_period_spend",
    "estimated_period_spend",
    "median_review_count",
):
    opportunity_rules[column] = ColumnRule("numeric", nullable=False, minimum=0)
opportunity_rules["demand_coverage_index"] = ColumnRule("numeric", minimum=0)
for column in ("avg_rating", "avg_quality_score"):
    opportunity_rules[column] = ColumnRule(
        "numeric", nullable=False, minimum=0, maximum=5
    )
opportunity_rules["city"] = ColumnRule(
    "string", nullable=False, allowed_values=frozenset({TARGET_CITY})
)
opportunity_rules["customer_preference"] = ColumnRule(
    "string",
    nullable=False,
    allowed_values=frozenset(CUSTOMER_PREFERENCES),
)
PREFERENCE_OPPORTUNITY_CONTRACT = DataContract(
    "preference_opportunity",
    opportunity_rules,
    unique_keys=(("city", "customer_preference"),),
    required_values={"customer_preference": frozenset(CUSTOMER_PREFERENCES)},
)

QUALITY_REPORT_CONTRACT = DataContract(
    "data_quality_report",
    {
        "dataset": ColumnRule("string", nullable=False),
        "step": ColumnRule("string", nullable=False),
        "rows": ColumnRule("integer", nullable=False, minimum=0),
        "columns": ColumnRule("integer", nullable=False, minimum=0),
        "missing_total": ColumnRule("integer", nullable=False, minimum=0),
        "duplicate_rows": ColumnRule("integer", nullable=False, minimum=0),
        "duplicate_ids": ColumnRule("numeric", minimum=0),
        "duplicate_yelp_ids": ColumnRule("numeric", minimum=0),
        "negative_frequency": ColumnRule("numeric", minimum=0),
        "missing_spend": ColumnRule("numeric", minimum=0),
        "invalid_age": ColumnRule("numeric", minimum=0),
        "rating_outside_0_5": ColumnRule("numeric", minimum=0),
    },
)

REJECTIONS_CONTRACT = DataContract(
    "data_rejections",
    {
        "dataset": ColumnRule("string", nullable=False),
        "step": ColumnRule("string", nullable=False),
        "reason": ColumnRule("string", nullable=False),
        "rows_rejected": ColumnRule("integer", nullable=False, minimum=0),
    },
    min_rows=1,
)


def validate_pipeline_contracts(
    customers_clean: pd.DataFrame,
    customers_miami: pd.DataFrame,
    yelp_clean: pd.DataFrame,
    customer_value: pd.DataFrame,
    preference_opportunity: pd.DataFrame,
    data_quality: pd.DataFrame,
    rejections: pd.DataFrame,
) -> None:
    checks = (
        (customers_clean, CUSTOMERS_CLEAN_CONTRACT),
        (customers_miami, CUSTOMERS_MIAMI_CONTRACT),
        (yelp_clean, YELP_CLEAN_CONTRACT),
        (customer_value, CUSTOMER_VALUE_CONTRACT),
        (preference_opportunity, PREFERENCE_OPPORTUNITY_CONTRACT),
        (data_quality, QUALITY_REPORT_CONTRACT),
        (rejections, REJECTIONS_CONTRACT),
    )
    for dataframe, contract in checks:
        validate_contract(dataframe, contract, stage="output")
