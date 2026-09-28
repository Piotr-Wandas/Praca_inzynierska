from __future__ import annotations
import pandas as pd

def assert_point_in_time(df: pd.DataFrame, cutoff_col: str = "cutoff_at") -> None:
    availability_cols = [c for c in df.columns if c.endswith("_available_at")]
    cutoff = pd.to_datetime(df[cutoff_col], utc=True)
    for col in availability_cols:
        available = pd.to_datetime(df[col], utc=True)
        bad = available.notna() & (available > cutoff)
        if bad.any():
            raise ValueError(f"Look-ahead detected in {col}: {int(bad.sum())} rows")

def asof_latest(observations: pd.DataFrame, cutoffs: pd.DataFrame, key: str, date_col: str = "available_at") -> pd.DataFrame:
    """Point-in-time as-of join; each cutoff sees only records already available."""
    left = cutoffs.copy().sort_values([key, "cutoff_at"])
    right = observations.copy().sort_values([key, date_col])
    left["cutoff_at"] = pd.to_datetime(left["cutoff_at"], utc=True)
    right[date_col] = pd.to_datetime(right[date_col], utc=True)
    return pd.merge_asof(left, right, left_on="cutoff_at", right_on=date_col, by=key, direction="backward")
