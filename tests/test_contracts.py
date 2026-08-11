import pandas as pd
import pytest

from src.config import FULL_PIPELINE_PATHS, SCHEMA_VERSION
from src.contracts import (
    CUSTOMERS_RAW_CONTRACT,
    ColumnRule,
    DataContract,
    DataContractError,
    validate_contract,
    validate_pipeline_contracts,
)


def test_input_contract_reports_missing_columns_with_context():
    incomplete = pd.DataFrame({"id_persona": [1]})

    with pytest.raises(DataContractError, match=r"customers_raw v1\.1\.0.*faltan columnas"):
        validate_contract(incomplete, CUSTOMERS_RAW_CONTRACT, stage="input")


def test_contract_reports_range_violations_before_writing():
    contract = DataContract(
        "sample",
        {"share": ColumnRule("numeric", nullable=False, minimum=0, maximum=1)},
    )

    with pytest.raises(DataContractError, match=r"mayores que 1"):
        validate_contract(pd.DataFrame({"share": [1.2]}), contract, stage="output")


def test_published_outputs_match_schema_version():
    paths = FULL_PIPELINE_PATHS
    validate_pipeline_contracts(
        pd.read_csv(paths.customers_clean),
        pd.read_csv(paths.customers_miami),
        pd.read_csv(paths.yelp_clean),
        pd.read_csv(paths.customer_value_miami),
        pd.read_csv(paths.preference_opportunity_miami),
        pd.read_csv(paths.restaurant_competition_miami),
        pd.read_csv(paths.preference_sensitivity_miami),
        pd.read_csv(paths.data_quality_report_csv),
        pd.read_csv(paths.data_rejections_csv),
    )

    assert SCHEMA_VERSION == "1.1.0"
