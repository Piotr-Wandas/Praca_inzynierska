import numpy as np
import pandas as pd

from financial_platform.modeling.feature_selection import select_usable_features


def test_empty_lag4_and_yoy_are_dropped_per_fold():
    frame = pd.DataFrame({
        "lag1": [1.0, 2.0, 3.0],
        "lag4": [np.nan, np.nan, np.nan],
        "yoy": [np.nan, np.nan, np.nan],
        "ticker": ["AAA", "AAA", "BBB"],
    })
    numeric, categorical, dropped = select_usable_features(
        frame, ["lag1", "lag4", "yoy"], ["ticker"], min_numeric_observations=2
    )
    assert numeric == ["lag1"]
    assert categorical == ["ticker"]
    assert dropped["lag4"] == "only_0_observed"
    assert dropped["yoy"] == "only_0_observed"


def test_lag4_returns_when_history_becomes_available():
    frame = pd.DataFrame({
        "lag1": [1.0, 2.0, 3.0, 4.0],
        "lag4": [np.nan, np.nan, 0.8, 1.1],
        "ticker": ["AAA"] * 4,
    })
    numeric, _, dropped = select_usable_features(
        frame, ["lag1", "lag4"], ["ticker"], min_numeric_observations=2
    )
    assert "lag4" in numeric
    assert "lag4" not in dropped
