import pandas as pd

from src.config import (
    TRANSACTION_ORDER,
    YELP_ALLOWED_CITIES,
    YELP_CLEAN,
)


def test_yelp_clean_has_traceable_ids():
    restaurants = pd.read_csv(YELP_CLEAN)

    assert restaurants["restaurant_id"].is_unique
    assert restaurants["yelp_id"].is_unique
    assert restaurants["rating"].between(0, 5).all()
    assert (restaurants["review_count"] >= 0).all()
    assert restaurants["city"].isin(YELP_ALLOWED_CITIES).all()
    assert restaurants.isna().sum().sum() == 0


def test_yelp_transactions_are_canonical():
    restaurants = pd.read_csv(YELP_CLEAN)
    reversed_delivery_pickup = f"{TRANSACTION_ORDER[1]}, {TRANSACTION_ORDER[0]}"

    assert restaurants["transactions"].str.contains(reversed_delivery_pickup).sum() == 0
    assert {"has_delivery", "has_pickup", "has_reservation"}.issubset(restaurants.columns)
