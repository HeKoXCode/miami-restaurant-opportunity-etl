import ast
import re

import pandas as pd

from .config import (
    MISSING_TEXT_VALUE,
    QUALITY_SCORE_MIN_REVIEWS,
    TRANSACTION_ORDER,
    YELP_ALLOWED_CITIES,
    YELP_RAW,
)


def parse_obj(value):
    # Al guardar la respuesta de Yelp en CSV, listas y diccionarios quedan como texto.
    # Esta función los recupera sin ejecutar contenido arbitrario.
    if isinstance(value, (list, dict)):
        return value
    if pd.isna(value):
        return None
    try:
        return ast.literal_eval(str(value))
    except (ValueError, SyntaxError):
        return None


def clean_text(value):
    if pd.isna(value):
        return pd.NA
    text = re.sub(r"\s+", " ", str(value).strip())
    return text if text else pd.NA


def clean_categories(value):
    parsed = parse_obj(value)
    if not isinstance(parsed, list):
        return MISSING_TEXT_VALUE

    categories = []
    for item in parsed:
        if isinstance(item, dict):
            title = clean_text(item.get("title"))
            if pd.notna(title):
                categories.append(str(title))

    return ", ".join(categories) if categories else MISSING_TEXT_VALUE


def clean_transactions(value):
    parsed = parse_obj(value)
    if not isinstance(parsed, list) or not parsed:
        return MISSING_TEXT_VALUE

    normalized = []
    for item in parsed:
        text = clean_text(item)
        if pd.notna(text):
            normalized.append(str(text).lower())

    ordered = [item for item in TRANSACTION_ORDER if item in set(normalized)]
    return ", ".join(ordered) if ordered else MISSING_TEXT_VALUE


def clean_phone(display_phone, phone):
    display_phone = clean_text(display_phone)
    if pd.notna(display_phone):
        return str(display_phone)

    if pd.notna(phone):
        digits = re.sub(r"\D", "", str(phone))
        if digits.endswith("0") and "." in str(phone):
            digits = digits[:-1]
        return digits if digits else MISSING_TEXT_VALUE

    return MISSING_TEXT_VALUE


def location_value(location_obj, key):
    if isinstance(location_obj, dict):
        return clean_text(location_obj.get(key))
    return pd.NA


def load_yelp(path=YELP_RAW):
    yelp = pd.read_csv(path, encoding="utf-8-sig")
    return yelp.drop(columns=["Unnamed: 0"], errors="ignore")


def clean_yelp(yelp_raw, rejection_audit=None):
    yelp_work = yelp_raw.drop_duplicates(subset=["id"]).copy()
    if rejection_audit is not None:
        rejection_audit["duplicate_yelp_id"] = len(yelp_raw) - len(yelp_work)
    yelp_clean = pd.DataFrame()

    # Construimos el output desde cero. Así queda claro qué campos de la API
    # entran al análisis y cuáles se dejan afuera.
    yelp_clean["restaurant_id"] = range(1, len(yelp_work) + 1)
    yelp_clean["yelp_id"] = yelp_work["id"].astype(str)
    yelp_clean["name"] = yelp_work["name"].apply(clean_text)

    yelp_clean["rating"] = pd.to_numeric(yelp_work["rating"], errors="coerce")
    yelp_clean["rating_was_missing"] = yelp_clean["rating"].isna()
    yelp_clean["rating"] = yelp_clean["rating"].fillna(yelp_clean["rating"].median())

    yelp_clean["review_count"] = pd.to_numeric(yelp_work["review_count"], errors="coerce")
    yelp_clean["review_count_was_missing"] = yelp_clean["review_count"].isna()
    yelp_clean["review_count"] = yelp_clean["review_count"].fillna(0).astype(int)

    yelp_clean["price"] = yelp_work["price"].apply(clean_text)
    yelp_clean["price_was_missing"] = yelp_clean["price"].isna()
    yelp_clean["price"] = yelp_clean["price"].fillna(MISSING_TEXT_VALUE)
    yelp_clean["price_level"] = yelp_clean["price"].apply(
        lambda value: len(value)
        if isinstance(value, str) and set(value) == {"$"}
        else 0
    ).astype(int)

    yelp_clean["phone"] = [
        clean_phone(display_phone, phone)
        for display_phone, phone in zip(yelp_work["display_phone"], yelp_work["phone"])
    ]
    yelp_clean["has_phone"] = yelp_clean["phone"].ne(MISSING_TEXT_VALUE)

    yelp_clean["categories"] = yelp_work["categories"].apply(clean_categories)
    yelp_clean["main_category"] = yelp_clean["categories"].apply(
        lambda value: value.split(", ")[0] if value != MISSING_TEXT_VALUE else MISSING_TEXT_VALUE
    )
    yelp_clean["category_count"] = yelp_clean["categories"].apply(
        lambda value: 0 if value == MISSING_TEXT_VALUE else len(str(value).split(", "))
    ).astype(int)

    yelp_clean["transactions"] = yelp_work["transactions"].apply(clean_transactions)
    yelp_clean["has_delivery"] = yelp_clean["transactions"].str.contains(
        "delivery", case=False, na=False
    )
    yelp_clean["has_pickup"] = yelp_clean["transactions"].str.contains(
        "pickup", case=False, na=False
    )
    yelp_clean["has_reservation"] = yelp_clean["transactions"].str.contains(
        "restaurant_reservation", case=False, na=False
    )

    coords = yelp_work["coordinates"].apply(parse_obj)
    yelp_clean["latitude"] = pd.to_numeric(
        coords.apply(lambda value: value.get("latitude") if isinstance(value, dict) else pd.NA),
        errors="coerce",
    )
    yelp_clean["longitude"] = pd.to_numeric(
        coords.apply(lambda value: value.get("longitude") if isinstance(value, dict) else pd.NA),
        errors="coerce",
    )

    location = yelp_work["location"].apply(parse_obj)
    # Las columnas de ubicación vienen dentro de un diccionario; aquí las dejamos planas.
    yelp_clean["address"] = location.apply(
        lambda value: ", ".join(value.get("display_address", []))
        if isinstance(value, dict) and value.get("display_address")
        else MISSING_TEXT_VALUE
    )
    yelp_clean["city"] = location.apply(lambda value: location_value(value, "city"))
    yelp_clean["state"] = location.apply(
        lambda value: location_value(value, "state")
    ).str.upper()
    yelp_clean["zip_code"] = (
        location.apply(lambda value: location_value(value, "zip_code"))
        .astype("string")
        .str.zfill(5)
    )
    yelp_clean["country"] = location.apply(
        lambda value: location_value(value, "country")
    ).str.upper()

    for column in ["city", "state", "zip_code", "country"]:
        mode_value = yelp_clean[column].mode(dropna=True)
        fallback = mode_value.iloc[0] if not mode_value.empty else MISSING_TEXT_VALUE
        yelp_clean[column] = yelp_clean[column].fillna(fallback)

    allowed_city = yelp_clean["city"].isin(YELP_ALLOWED_CITIES)
    if rejection_audit is not None:
        rejection_audit["outside_allowed_city"] = int((~allowed_city).sum())
    yelp_clean = yelp_clean.loc[allowed_city].copy()

    duplicate_location = yelp_clean.duplicated(subset=["name", "address"])
    if rejection_audit is not None:
        rejection_audit["duplicate_name_address"] = int(duplicate_location.sum())
    yelp_clean = yelp_clean.loc[~duplicate_location].reset_index(drop=True)
    yelp_clean["restaurant_id"] = range(1, len(yelp_clean) + 1)

    observed_price = yelp_clean["price"].ne(MISSING_TEXT_VALUE)
    # Para precio usamos el dato más cercano disponible: ciudad y categoría,
    # después categoría y, como último recurso, la moda general.
    price_by_city_category = (
        yelp_clean.loc[observed_price]
        .groupby(["city", "main_category"])["price"]
        .agg(lambda value: value.mode().iloc[0] if not value.mode().empty else pd.NA)
    )
    price_by_category = (
        yelp_clean.loc[observed_price]
        .groupby("main_category")["price"]
        .agg(lambda value: value.mode().iloc[0] if not value.mode().empty else pd.NA)
    )
    general_price = yelp_clean.loc[observed_price, "price"].mode().iloc[0]

    def impute_price(row):
        if row["price"] != MISSING_TEXT_VALUE:
            return row["price"]

        key = (row["city"], row["main_category"])
        if key in price_by_city_category.index:
            return price_by_city_category.loc[key]

        if row["main_category"] in price_by_category.index:
            return price_by_category.loc[row["main_category"]]

        return general_price

    yelp_clean["price"] = yelp_clean.apply(impute_price, axis=1)
    yelp_clean["price_level"] = yelp_clean["price"].apply(
        lambda value: len(value)
        if isinstance(value, str) and set(value) == {"$"}
        else 0
    ).astype(int)

    average_rating = yelp_clean["rating"].mean()
    min_reviews = QUALITY_SCORE_MIN_REVIEWS
    # Un 5 con pocas reseñas no debería pesar igual que un 4.5 con cientos.
    # El score acerca los casos con poca evidencia al promedio de la muestra.
    yelp_clean["quality_score"] = (
        (yelp_clean["review_count"] / (yelp_clean["review_count"] + min_reviews))
        * yelp_clean["rating"]
        + (min_reviews / (yelp_clean["review_count"] + min_reviews)) * average_rating
    ).round(2)

    final_columns = [
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

    return yelp_clean[final_columns]
