from __future__ import annotations

import pandas as pd


def rank_models(results: pd.DataFrame, metric: str = "mae") -> pd.DataFrame:
    if metric not in results.columns:
        raise ValueError(f"Unknown metric: {metric}")
    return results.sort_values(metric, ascending=True).reset_index(drop=True)


def summarize_by_model(fold_results: pd.DataFrame) -> pd.DataFrame:
    metrics = [c for c in ["mae", "rmse", "medae", "smape", "wape", "r2"] if c in fold_results]
    return (
        fold_results.groupby("model", as_index=False)[metrics]
        .mean(numeric_only=True)
        .sort_values("mae")
        .reset_index(drop=True)
    )
