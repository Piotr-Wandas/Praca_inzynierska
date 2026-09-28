from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from financial_platform.datasets.panel_builder import prepare_modeling_panel
from financial_platform.evaluation.comparison import summarize_by_model
from financial_platform.evaluation.metrics import regression_metrics
from financial_platform.modeling.model_factory import (
    make_hist_gradient_boosting,
    make_random_forest,
    make_ridge,
)


@dataclass(frozen=True)
class ExperimentConfig:
    target: str = "target_net_income"
    period_col: str = "period_end"
    min_train_periods: int = 8


def _walk_forward_splits(df: pd.DataFrame, period_col: str, min_train_periods: int):
    periods = sorted(pd.to_datetime(df[period_col]).dropna().unique())
    for i in range(min_train_periods, len(periods)):
        train_periods = periods[:i]
        valid_period = periods[i]
        train_idx = df[pd.to_datetime(df[period_col]).isin(train_periods)].index
        valid_idx = df[pd.to_datetime(df[period_col]) == valid_period].index
        if len(train_idx) and len(valid_idx):
            yield i - min_train_periods + 1, valid_period, train_idx, valid_idx


def run_experiment(
    df: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
    config: ExperimentConfig | None = None,
    enable_mlflow: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    config = config or ExperimentConfig()
    panel = prepare_modeling_panel(df)

    models = {
        "ridge": make_ridge(numeric_features, categorical_features),
        "random_forest": make_random_forest(numeric_features, categorical_features),
        "hist_gradient_boosting": make_hist_gradient_boosting(numeric_features, categorical_features),
    }

    fold_rows: list[dict] = []
    pred_rows: list[dict] = []

    for fold, valid_period, train_idx, valid_idx in _walk_forward_splits(
        panel, config.period_col, config.min_train_periods
    ):
        train = panel.loc[train_idx].copy()
        valid = panel.loc[valid_idx].copy()
        y_train = train[config.target]
        y_valid = valid[config.target]

        # Baselines use only historical target information already present as lags.
        baseline_predictions = {}
        if "net_income_lag1" in valid:
            baseline_predictions["baseline_last_value"] = valid["net_income_lag1"].to_numpy()
        if "net_income_lag4" in valid:
            baseline_predictions["baseline_seasonal"] = valid["net_income_lag4"].to_numpy()

        for model_name, y_pred in baseline_predictions.items():
            mask = ~pd.isna(y_pred) & ~pd.isna(y_valid.to_numpy())
            if not mask.any():
                continue
            metrics = regression_metrics(y_valid.to_numpy()[mask], y_pred[mask])
            fold_rows.append({"fold": fold, "period": str(valid_period), "model": model_name, **metrics})
            for idx, pred in zip(valid.index[mask], y_pred[mask]):
                pred_rows.append({"row_index": int(idx), "model": model_name, "prediction": float(pred)})

        X_train = train[numeric_features + categorical_features]
        X_valid = valid[numeric_features + categorical_features]

        for model_name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_valid)
            metrics = regression_metrics(y_valid, y_pred)
            fold_rows.append({"fold": fold, "period": str(valid_period), "model": model_name, **metrics})
            for idx, pred in zip(valid.index, y_pred):
                pred_rows.append({"row_index": int(idx), "model": model_name, "prediction": float(pred)})

            if enable_mlflow:
                import mlflow
                with mlflow.start_run(run_name=f"{model_name}-fold-{fold}", nested=True):
                    mlflow.log_param("model", model_name)
                    mlflow.log_param("fold", fold)
                    mlflow.log_param("validation_period", str(valid_period))
                    mlflow.log_metrics({k: v for k, v in metrics.items() if np.isfinite(v)})

    folds = pd.DataFrame(fold_rows)
    summary = summarize_by_model(folds) if not folds.empty else pd.DataFrame()
    return folds, summary


def save_experiment_outputs(folds: pd.DataFrame, summary: pd.DataFrame, output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    folds.to_csv(out / "fold_metrics.csv", index=False)
    summary.to_csv(out / "model_comparison.csv", index=False)
