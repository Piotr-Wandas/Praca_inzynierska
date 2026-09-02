import pandas as pd

def add_lag_features(df: pd.DataFrame, value_col: str, group_col: str = "ticker") -> pd.DataFrame:
    out = df.sort_values([group_col, "period_end"]).copy()
    g = out.groupby(group_col, sort=False)[value_col]
    out[f"{value_col}_lag1"] = g.shift(1)
    out[f"{value_col}_lag4"] = g.shift(4)
    out[f"{value_col}_yoy_change"] = (out[value_col] - out[f"{value_col}_lag4"]) / out[f"{value_col}_lag4"].abs().replace(0, pd.NA)
    out[f"{value_col}_rolling4"] = g.transform(lambda s: s.shift(1).rolling(4, min_periods=2).mean())
    return out
