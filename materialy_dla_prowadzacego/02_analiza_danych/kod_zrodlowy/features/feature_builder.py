from __future__ import annotations

import pandas as pd

from financial_platform.features.financial import add_lag_features


def build_panel_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Build the feature set used by the semester-II model comparison.

    The function assumes that the input panel was already assembled point-in-time,
    i.e. every source value satisfies available_at <= cutoff_at.
    """
    required = {"ticker", "period_end", "cutoff_at", "target_net_income"}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"Missing panel columns: {sorted(missing)}")

    out = panel.copy()
    out["period_end"] = pd.to_datetime(out["period_end"])
    out["cutoff_at"] = pd.to_datetime(out["cutoff_at"], utc=True)
    out = out.sort_values(["ticker", "period_end"])

    # Only derive target-history features if they are not already supplied.
    if "net_income_lag1" not in out.columns:
        source = out[["ticker", "period_end", "target_net_income"]].rename(
            columns={"target_net_income": "net_income"}
        )
        derived = add_lag_features(source, value_col="net_income")
        out["net_income_lag1"] = derived["net_income_lag1"]
        out["net_income_lag4"] = derived["net_income_lag4"]
        out["net_income_yoy_change"] = derived["net_income_yoy_change"]
        out["net_income_rolling4"] = derived["net_income_rolling4"]

    out["quarter"] = out["period_end"].dt.quarter.astype(str)
    return out.reset_index(drop=True)
