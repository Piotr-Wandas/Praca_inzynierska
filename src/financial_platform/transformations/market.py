from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"trade_date", "open", "high", "low", "close"}


def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize OHLCV data without using future information."""
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing market columns: {sorted(missing)}")

    out = df.copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"], errors="raise")
    for col in ["open", "high", "low", "close", "volume"]:
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out = out.drop_duplicates(subset=[c for c in ["ticker", "trade_date"] if c in out.columns])
    out = out.sort_values([c for c in ["ticker", "trade_date"] if c in out.columns])

    invalid = (
        (out["high"] < out[["open", "low", "close"]].max(axis=1))
        | (out["low"] > out[["open", "high", "close"]].min(axis=1))
    )
    if invalid.any():
        raise ValueError(f"Invalid OHLC rows: {int(invalid.sum())}")
    if "volume" in out and (out["volume"].dropna() < 0).any():
        raise ValueError("Negative volume detected")
    return out.reset_index(drop=True)
