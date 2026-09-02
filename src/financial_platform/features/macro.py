from __future__ import annotations

import pandas as pd


def add_macro_lags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values(["series_code", "observation_date"])
    g = out.groupby("series_code", group_keys=False)
    out["macro_change_1"] = g["value"].pct_change(1)
    out["macro_lag_1"] = g["value"].shift(1)
    out["macro_lag_3"] = g["value"].shift(3)
    return out
