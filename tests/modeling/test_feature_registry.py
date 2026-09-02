import pandas as pd

from financial_platform.modeling.feature_registry import (
    applicable_mask,
    feature_candidates_for_target,
)
from financial_platform.modeling.feature_registry import scoped_feature_coverage


def test_financial_feature_coverage_uses_only_financial_denominator():
    frame = pd.DataFrame({
        "ticker": ["BANK1", "BANK1", "IND1", "IND1"],
        "is_financial": [True, True, False, False],
        "net_interest_income_lag1": [10.0, 11.0, None, None],
    })
    row = scoped_feature_coverage(frame, ["net_interest_income_lag1"])[0]
    assert row["eligible_rows"] == 2
    assert row["observed"] == 2
    assert row["coverage"] == 1.0
    assert row["global_coverage"] == 0.5
    assert row["scope"] == "financial"


def test_nonfinancial_feature_coverage_uses_only_nonfinancial_denominator():
    frame = pd.DataFrame({
        "ticker": ["BANK1", "BANK1", "IND1", "IND1"],
        "is_financial": [True, True, False, False],
        "revenue_lag1": [None, None, 100.0, 110.0],
    })
    row = scoped_feature_coverage(frame, ["revenue_lag1"])[0]
    assert row["eligible_rows"] == 2
    assert row["coverage"] == 1.0
    assert row["scope"] == "non_financial"


def test_global_net_income_target_excludes_sector_specific_features():
    numeric, categorical = feature_candidates_for_target(
        "all",
        ["net_income_lag1", "revenue_lag1", "net_interest_income_lag1", "return_20d"],
        ["ticker", "sector"],
    )
    assert numeric == ["net_income_lag1", "return_20d"]
    assert categorical == ["ticker", "sector"]


def test_financial_target_keeps_global_and_financial_features():
    numeric, _ = feature_candidates_for_target(
        "financial",
        ["net_income_lag1", "revenue_lag1", "net_interest_income_lag1", "return_20d"],
        [],
    )
    assert numeric == ["net_income_lag1", "net_interest_income_lag1", "return_20d"]
