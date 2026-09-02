import pandas as pd

def last_value_baseline(df: pd.DataFrame, target: str) -> pd.Series:
    return df.groupby("ticker", sort=False)[target].shift(1)

def seasonal_yoy_baseline(df: pd.DataFrame, target: str) -> pd.Series:
    return df.groupby("ticker", sort=False)[target].shift(4)
