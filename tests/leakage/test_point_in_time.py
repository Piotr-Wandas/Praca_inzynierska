import pandas as pd
import pytest
from financial_platform.datasets.point_in_time import assert_point_in_time

def test_future_feature_is_rejected():
    df = pd.DataFrame({"cutoff_at":["2025-05-01T00:00:00Z"],"macro_available_at":["2025-05-02T00:00:00Z"]})
    with pytest.raises(ValueError, match="Look-ahead"):
        assert_point_in_time(df)

def test_past_feature_is_allowed():
    df = pd.DataFrame({"cutoff_at":["2025-05-02T00:00:00Z"],"macro_available_at":["2025-05-01T00:00:00Z"]})
    assert_point_in_time(df)
