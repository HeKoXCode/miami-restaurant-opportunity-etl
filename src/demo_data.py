"""Generate a deterministic, fully synthetic customer source for public demos."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    CUSTOMER_PREFERENCES,
    DEMO_DEFAULT_ROWS,
    DEMO_DEFAULT_SEED,
    ESTRATOS,
    SCHEMA_VERSION,
)

CITIES = ["Miami", "Orlando", "Tampa", "Fort Lauderdale"]


def _apply_quality_scenarios(customers: pd.DataFrame) -> None:
    """Add known dirty cases so the demo exercises the cleaning rules."""
    customers.loc[customers.index[::97], "frecuencia_visita"] = -1
    customers.loc[customers.index[17::101], "promedio_gasto_comida"] = np.nan

    unusable_frequency = customers.index[31::113]
    customers.loc[unusable_frequency, "frecuencia_visita"] = -1
    customers.loc[unusable_frequency, "promedio_gasto_comida"] = np.nan

    missing_activity = customers.index[43::127]
    customers.loc[missing_activity, "frecuencia_visita"] = np.nan
    customers.loc[missing_activity, "promedio_gasto_comida"] = 0

    customers.loc[customers.index[11::89], "edad"] = 105
    inactive_invalid_age = customers.index[59::137]
    customers.loc[inactive_invalid_age, "edad"] = 15
    customers.loc[inactive_invalid_age, "frecuencia_visita"] = 0
    customers.loc[inactive_invalid_age, "promedio_gasto_comida"] = 0
    customers.loc[customers.index[23::67], "preferencias_alimenticias"] = pd.NA


def generate_demo_customers(
    output_path: Path,
    rows: int = DEMO_DEFAULT_ROWS,
    seed: int = DEMO_DEFAULT_SEED,
) -> pd.DataFrame:
    if not 300 <= rows <= 1000:
        raise ValueError("La demo pública debe contener entre 300 y 1.000 clientes.")

    rng = np.random.default_rng(seed)
    row_number = np.arange(rows)
    strata = rng.choice(ESTRATOS, size=rows, p=[0.23, 0.34, 0.27, 0.16])
    premium_probability = {
        "Bajo": 0.12,
        "Medio": 0.32,
        "Alto": 0.67,
        "Muy Alto": 0.88,
    }
    premium = np.array(
        [
            "Sí" if value < premium_probability[stratum] else "No"
            for value, stratum in zip(rng.random(rows), strata)
        ]
    )
    spend_base = {
        "Bajo": 24,
        "Medio": 39,
        "Alto": 67,
        "Muy Alto": 104,
    }
    spend = np.array(
        [max(8, rng.normal(spend_base[stratum], 9)) for stratum in strata]
    ).round(2)

    customers = pd.DataFrame(
        {
            "id_persona": 9_000_000_000 + row_number,
            "nombre": [f"Cliente Demo {index:04d}" for index in row_number],
            "apellido": "Sintético",
            "edad": rng.integers(18, 86, size=rows).astype(float),
            "genero": rng.choice(
                ["Femenino", "Masculino", "No binario"],
                size=rows,
                p=[0.48, 0.48, 0.04],
            ),
            "ciudad_residencia": rng.choice(
                CITIES,
                size=rows,
                p=[0.66, 0.13, 0.11, 0.10],
            ),
            "estrato_socioeconomico": strata,
            "frecuencia_visita": rng.integers(1, 13, size=rows).astype(float),
            "promedio_gasto_comida": spend,
            "ocio": rng.choice(["Sí", "No"], size=rows, p=[0.72, 0.28]),
            "consume_licor": rng.choice(["Sí", "No"], size=rows, p=[0.57, 0.43]),
            "preferencias_alimenticias": rng.choice(
                CUSTOMER_PREFERENCES,
                size=rows,
                p=[0.24, 0.11, 0.18, 0.22, 0.12, 0.13],
            ).astype(object),
            "membresia_premium": premium,
            "telefono_contacto": [
                f"+1-202-555-{100 + index % 100:04d}" for index in row_number
            ],
            "correo_electronico": [
                f"cliente-demo-{index:04d}@example.invalid" for index in row_number
            ],
            "tipo_de_pago_mas_usado": rng.choice(
                ["Tarjeta", "Efectivo", "Billetera digital"],
                size=rows,
                p=[0.58, 0.19, 0.23],
            ),
            "ingresos_mensuales": np.array(
                [
                    max(900, rng.normal(spend_base[stratum] * 95, 850))
                    for stratum in strata
                ]
            ).round(0),
        }
    )
    customers.loc[
        : len(CUSTOMER_PREFERENCES) - 1,
        "preferencias_alimenticias",
    ] = CUSTOMER_PREFERENCES
    _apply_quality_scenarios(customers)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    customers.to_csv(output_path, index=False, encoding="utf-8")
    return customers


def save_generation_metadata(
    output_path: Path,
    customers_path: Path,
    rows: int,
    seed: int,
) -> None:
    metadata = {
        "dataset": "customers_demo_raw",
        "fully_synthetic": True,
        "generator": "src.demo_data.generate_demo_customers",
        "rows": rows,
        "seed": seed,
        "schema_version": SCHEMA_VERSION,
        "output_file": customers_path.name,
        "contact_data_policy": "Reserved 555 numbers and example.invalid emails only",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
