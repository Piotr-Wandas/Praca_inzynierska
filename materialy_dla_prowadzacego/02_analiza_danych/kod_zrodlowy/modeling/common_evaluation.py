from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from financial_platform.evaluation.metrics import regression_metrics


@dataclass(frozen=True)
class TargetSpec:
    key: str
    target_column: str
    target_code: str
    lag1_column: str
    lag4_column: str
    label_pl: str
    applicability: str = "all"


TARGET_SPECS = {
    "net_income": TargetSpec(
        "net_income", "target_net_income", "NET_INCOME_CANONICAL",
        "net_income_lag1", "net_income_lag4", "Zysk netto t+1", "all",
    ),
    "revenue": TargetSpec(
        "revenue", "target_revenue", "REVENUE",
        "revenue_lag1", "revenue_lag4", "Przychody t+1", "non_financial",
    ),
    "net_interest_income": TargetSpec(
        "net_interest_income", "target_net_interest_income", "NET_INTEREST_INCOME",
        "net_interest_income_lag1", "net_interest_income_lag4", "Wynik odsetkowy t+1", "financial",
    ),
}

# Zgodność wsteczna z v5.2.
COMMON_EVAL_REQUIRED = ["target_net_income", "net_income_lag1", "net_income_lag4"]


def get_target_spec(target: str) -> TargetSpec:
    try:
        return TARGET_SPECS[target]
    except KeyError as exc:
        raise ValueError(f"Nieznany target {target!r}. Dostępne: {', '.join(TARGET_SPECS)}") from exc


def common_eval_mask(frame: pd.DataFrame, target: str = "net_income") -> pd.Series:
    spec = get_target_spec(target)
    mask = pd.Series(True, index=frame.index)
    for col in [spec.target_column, spec.lag1_column, spec.lag4_column]:
        if col not in frame.columns:
            return pd.Series(False, index=frame.index)
        mask &= frame[col].notna()
    if spec.applicability == "financial" and "is_financial" in frame:
        mask &= frame["is_financial"].astype(bool)
    elif spec.applicability == "non_financial" and "is_financial" in frame:
        mask &= ~frame["is_financial"].astype(bool)
    return mask


def summary_from_oof(prediction_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for model_name, group in prediction_df.groupby("model_name"):
        metrics = regression_metrics(group["actual_value"], group["predicted_value"])
        rows.append({
            "model": model_name,
            **metrics,
            "n_obs": int(len(group)),
            "folds": int(group["fold"].nunique()),
            "companies": int(group["ticker"].nunique()),
            "evaluation_from": str(pd.to_datetime(group["target_period_end"]).min().date()),
            "evaluation_to": str(pd.to_datetime(group["target_period_end"]).max().date()),
        })
    return pd.DataFrame(rows).sort_values(["mae", "model"]).reset_index(drop=True)
