from __future__ import annotations

import pandas as pd


def clean_macro_data(df: pd.DataFrame) -> pd.DataFrame:
    required = {"series_code", "observation_date", "value", "available_at"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing macro columns: {sorted(missing)}")
    out = df.copy()
    out["observation_date"] = pd.to_datetime(out["observation_date"], errors="raise")
    out["available_at"] = pd.to_datetime(out["available_at"], utc=True, errors="raise")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.drop_duplicates(["series_code", "observation_date", "available_at"]).sort_values(
        ["series_code", "available_at"]
    ).reset_index(drop=True)
