import pandas as pd

def validate_ohlcv(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    required = {"open", "high", "low", "close"}
    if not required.issubset(df.columns):
        return [f"missing columns: {sorted(required - set(df.columns))}"]
    if (df["high"] < df[["open", "low", "close"]].max(axis=1)).any():
        errors.append("high below another OHLC value")
    if (df["low"] > df[["open", "high", "close"]].min(axis=1)).any():
        errors.append("low above another OHLC value")
    if "volume" in df.columns and (df["volume"].dropna() < 0).any():
        errors.append("negative volume")
    return errors
