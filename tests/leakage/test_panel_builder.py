import pandas as pd
import pytest

from financial_platform.datasets.panel_builder import assert_point_in_time


def test_point_in_time_rejects_future_feature():
    df = pd.DataFrame({
        "cutoff_at": ["2025-05-20T00:00:00Z"],
        "fundamental_available_at": ["2025-05-21T00:00:00Z"],
    })
    with pytest.raises(ValueError, match="Look-ahead"):
        assert_point_in_time(df, ["fundamental_available_at"])
