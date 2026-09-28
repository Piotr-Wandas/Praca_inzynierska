from __future__ import annotations

import pandas as pd


def assert_point_in_time(df: pd.DataFrame, availability_columns: list[str], cutoff_col: str = "cutoff_at") -> None:
    cutoff = pd.to_datetime(df[cutoff_col], utc=True)
    for col in availability_columns:
        if col not in df.columns:
            continue
        available = pd.to_datetime(df[col], utc=True)
        violation = available > cutoff
        if violation.any():
            rows = df.index[violation].tolist()[:10]
            raise ValueError(f"Look-ahead detected in {col}; example rows: {rows}")


def prepare_modeling_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Validate time consistency and sort panel chronologically."""
    availability = [
        "fundamental_available_at",
        "market_available_at",
        "macro_available_at",
    ]
    out = df.copy()
    out["period_end"] = pd.to_datetime(out["period_end"])
    out["cutoff_at"] = pd.to_datetime(out["cutoff_at"], utc=True)
    assert_point_in_time(out, availability)
    return out.sort_values(["period_end", "ticker"]).reset_index(drop=True)
