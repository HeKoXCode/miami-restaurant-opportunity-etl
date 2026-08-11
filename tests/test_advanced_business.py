import pandas as pd

from src.business import (
    build_preference_sensitivity,
    build_restaurant_competition,
)
from src.config import (
    CATEGORY_MAPPING,
    PREFERENCE_OPPORTUNITY_MIAMI,
    YELP_CLEAN,
)


def test_competition_mart_covers_every_preference_and_price_level():
    competition = build_restaurant_competition(
        pd.read_csv(YELP_CLEAN),
        pd.read_csv(CATEGORY_MAPPING),
    )

    assert len(competition) == 30
    assert set(competition["price_level"]) == {0, 1, 2, 3, 4}
    assert competition.groupby("customer_preference").size().eq(5).all()
    assert competition["restaurant_share_within_preference"].between(0, 1).all()
    assert competition.groupby("customer_preference")[
        "restaurant_share_within_preference"
    ].sum().round(3).eq(1).all()
    assert (
        competition["imputed_price_count"] <= competition["restaurant_count"]
    ).all()


def test_sensitivity_mart_exposes_three_threshold_scenarios():
    sensitivity = build_preference_sensitivity(
        pd.read_csv(PREFERENCE_OPPORTUNITY_MIAMI)
    )

    assert len(sensitivity) == 18
    assert set(sensitivity["scenario"]) == {
        "Conservador",
        "Base",
        "Exploratorio",
    }
    assert sensitivity.groupby("customer_preference").size().eq(3).all()
    assert sensitivity["stable_across_scenarios"].dtype == bool


def test_base_sensitivity_matches_published_signal():
    opportunity = pd.read_csv(PREFERENCE_OPPORTUNITY_MIAMI)
    sensitivity = build_preference_sensitivity(opportunity)
    base = sensitivity.loc[sensitivity["scenario"] == "Base"]
    expected = opportunity.set_index("customer_preference")["coverage_signal"]

    assert base.set_index("customer_preference")["coverage_signal"].to_dict() == (
        expected.to_dict()
    )
