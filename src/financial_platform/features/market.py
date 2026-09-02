from __future__ import annotations

import numpy as np
import pandas as pd


def add_market_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create lagged market features per company.

    All rolling statistics are based on information at or before a given trade date.
    """
    out = df.copy().sort_values(["ticker", "trade_date"])
    g = out.groupby("ticker", group_keys=False)

    out["return_5d"] = g["close"].pct_change(5)
    out["return_20d"] = g["close"].pct_change(20)
    out["return_60d"] = g["close"].pct_change(60)
    out["return_120d"] = g["close"].pct_change(120)

    daily_return = g["close"].pct_change()
    out["volatility_20d"] = daily_return.groupby(out["ticker"]).transform(
        lambda s: s.rolling(20, min_periods=10).std() * np.sqrt(252)
    )
    out["volatility_60d"] = daily_return.groupby(out["ticker"]).transform(
        lambda s: s.rolling(60, min_periods=30).std() * np.sqrt(252)
    )

    if "volume" in out.columns:
        avg_volume = g["volume"].transform(lambda s: s.rolling(20, min_periods=5).mean())
        out["volume_ratio_20d"] = out["volume"] / avg_volume.replace(0, np.nan)

    rolling_peak = g["close"].transform(lambda s: s.rolling(252, min_periods=20).max())
    out["distance_from_52w_high"] = out["close"] / rolling_peak - 1.0
    return out
