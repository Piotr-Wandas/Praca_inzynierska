from __future__ import annotations

import pandas as pd

NUMERIC_CANDIDATES = [
    "net_income_lag1", "net_income_lag4", "net_income_yoy",
    "revenue_lag1", "revenue_lag4", "revenue_yoy",
    "operating_profit_lag1", "total_assets_lag1", "equity_lag1",
    "net_interest_income_lag1", "net_interest_income_lag4", "net_interest_income_yoy",
    "net_fee_income_lag1", "net_fee_income_lag4", "net_fee_income_yoy",
    "return_20d", "return_60d", "volatility_20d", "volume_ratio_20d",
    "fx_eurpln", "fx_usdpln", "fx_chfpln",
]
CATEGORICAL_CANDIDATES = ["ticker", "sector", "quarter", "net_income_source"]


def select_usable_features(
    frame: pd.DataFrame,
    numeric_candidates: list[str],
    categorical_candidates: list[str],
    min_numeric_observations: int = 2,
) -> tuple[list[str], list[str], dict[str, str]]:
    """Wybiera tylko cechy mające uczące wartości w konkretnym foldzie."""
    numeric: list[str] = []
    categorical: list[str] = []
    dropped: dict[str, str] = {}

    for col in numeric_candidates:
        if col not in frame.columns:
            dropped[col] = "missing_column"
            continue
        observed = int(pd.to_numeric(frame[col], errors="coerce").notna().sum())
        if observed < min_numeric_observations:
            dropped[col] = f"only_{observed}_observed"
        else:
            numeric.append(col)

    for col in categorical_candidates:
        if col not in frame.columns:
            dropped[col] = "missing_column"
            continue
        observed = int(frame[col].notna().sum())
        if observed == 0:
            dropped[col] = "no_observed_values"
        else:
            categorical.append(col)

    return numeric, categorical, dropped
