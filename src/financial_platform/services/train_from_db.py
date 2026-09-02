from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text

from financial_platform.config.settings import get_settings
from financial_platform.db.session import get_engine
from financial_platform.evaluation.metrics import regression_metrics
from financial_platform.modeling.model_factory import (
    make_hist_gradient_boosting,
    make_random_forest,
    make_ridge,
)
from financial_platform.modeling.feature_selection import (
    CATEGORICAL_CANDIDATES,
    NUMERIC_CANDIDATES,
    select_usable_features,
)
from financial_platform.modeling.feature_registry import feature_candidates_for_target
from financial_platform.modeling.common_evaluation import (
    TargetSpec,
    common_eval_mask,
    get_target_spec,
    summary_from_oof,
)
from financial_platform.services.model_dataset import build_dataset_from_db


def _applicable(frame: pd.DataFrame, spec: TargetSpec) -> pd.DataFrame:
    if spec.applicability == "financial" and "is_financial" in frame:
        return frame[frame["is_financial"].astype(bool)].copy()
    if spec.applicability == "non_financial" and "is_financial" in frame:
        return frame[~frame["is_financial"].astype(bool)].copy()
    return frame.copy()


def _splits(df: pd.DataFrame, spec: TargetSpec, min_train_periods: int = 8):
    df = _applicable(df, spec)
    periods = sorted(pd.to_datetime(df["period_end"]).dropna().unique())
    for i in range(min_train_periods, len(periods)):
        valid_period = periods[i]
        train = df[pd.to_datetime(df["period_end"]) < valid_period].copy()
        valid = df[pd.to_datetime(df["period_end"]) == valid_period].copy()
        train = train[train[spec.target_column].notna()]
        valid = valid[common_eval_mask(valid, spec.key)]
        if len(train) >= 15 and len(valid) >= 1:
            yield i, valid_period, train, valid


def _make_models(numeric: list[str], categorical: list[str]):
    return {
        "ridge": make_ridge(numeric, categorical),
        "random_forest": make_random_forest(numeric, categorical),
        "hist_gradient_boosting": make_hist_gradient_boosting(numeric, categorical),
    }


def _json_safe(value):
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return None if pd.isna(value) or not np.isfinite(value) else float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def _create_training_context(
    conn, df: pd.DataFrame, feature_count: int, spec: TargetSpec
) -> tuple[int, int, str]:
    experiment_name = f"{spec.key}-quarterly-real-data-v55"
    exp_id = conn.execute(text("""
        INSERT INTO ml.experiment(name, description, target_code)
        VALUES (:name, :description, :target_code)
        ON CONFLICT (name) DO UPDATE SET
            description=EXCLUDED.description, target_code=EXCLUDED.target_code
        RETURNING id
    """), {
        "name": experiment_name,
        "description": (
            f"v5.5 sector-aware common-sample walk-forward; target={spec.label_pl}; "
            "structural missingness handled by target-aware feature scopes"
        ),
        "target_code": spec.target_code,
    }).scalar_one()

    version_code = f"v55-{spec.key}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    dataset_id = conn.execute(text("""
        INSERT INTO ml.dataset_version(
            version_code, created_at, cutoff_from, cutoff_to, row_count, feature_count, notes
        ) VALUES (
            :code, now(), :cutoff_from, :cutoff_to, :row_count, :feature_count, :notes
        ) RETURNING id
    """), {
        "code": version_code,
        "cutoff_from": df["cutoff_at"].min(),
        "cutoff_to": df["cutoff_at"].max(),
        "row_count": int(len(df)),
        "feature_count": int(feature_count),
        "notes": f"v5.5 point-in-time panel; target={spec.key}; common OOF; sector-aware feature scopes",
    }).scalar_one()
    return exp_id, dataset_id, version_code


def _save_run(
    conn,
    *,
    exp_id: int,
    dataset_id: int,
    spec: TargetSpec,
    model_name: str,
    metrics: dict,
    train_from,
    train_to,
    valid_from,
    valid_to,
    artifact_uri: str,
    hyperparameters: dict,
) -> int:
    return conn.execute(text("""
        INSERT INTO ml.training_run(
            experiment_id, dataset_version_id, model_name, target_code,
            train_from, train_to, validation_from, validation_to,
            hyperparameters, metrics, artifact_uri, status
        ) VALUES (
            :exp_id, :dataset_id, :model_name, :target_code,
            :train_from, :train_to, :valid_from, :valid_to,
            CAST(:hyperparameters AS jsonb), CAST(:metrics AS jsonb), :artifact_uri, 'completed'
        ) RETURNING id
    """), {
        "exp_id": exp_id,
        "dataset_id": dataset_id,
        "model_name": model_name,
        "target_code": spec.target_code,
        "train_from": train_from,
        "train_to": train_to,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "metrics": json.dumps(_json_safe(metrics), ensure_ascii=False),
        "hyperparameters": json.dumps(_json_safe(hyperparameters), ensure_ascii=False),
        "artifact_uri": artifact_uri,
    }).scalar_one()


def train_models_from_db(target: str = "net_income", min_common_eval_rows: int = 20) -> dict:
    """Trenuje modele na jednej, wspólnej próbce OOF dla wskazanego targetu.

    target:
      - net_income: kanoniczny zysk netto t+1 (cały panel),
      - revenue: przychody t+1 (tylko spółki niefinansowe),
      - net_interest_income: wynik odsetkowy t+1 (tylko sektor finansowy).
    """
    spec = get_target_spec(target)
    df = build_dataset_from_db()
    if df.empty:
        raise RuntimeError("Baza nie zawiera danych do trenowania. Najpierw uruchom pobieranie danych.")

    applicable = _applicable(df, spec)
    known_target_rows = int(applicable[spec.target_column].notna().sum()) if spec.target_column in applicable else 0
    raw_common_rows = int(common_eval_mask(applicable, spec.key).sum())
    raw_common_periods = int(applicable.loc[common_eval_mask(applicable, spec.key), "target_period_end"].nunique()) if raw_common_rows else 0
    if raw_common_rows < min_common_eval_rows:
        raise RuntimeError(
            f"Niewystarczająca wspólna próbka dla targetu {spec.key}: {raw_common_rows} obserwacji "
            f"(minimum {min_common_eval_rows}). Najpierw uruchom v5.3 mapping audit i ponownie pobierz fundamenty."
        )

    raw_numeric_candidates = [c for c in NUMERIC_CANDIDATES if c in df.columns]
    raw_categorical_candidates = [c for c in CATEGORICAL_CANDIDATES if c in df.columns]
    numeric_candidates, categorical_candidates = feature_candidates_for_target(
        spec.applicability, raw_numeric_candidates, raw_categorical_candidates
    )
    if not numeric_candidates:
        raise RuntimeError("Brak kandydatów cech liczbowych do trenowania.")

    fold_metric_rows: list[dict] = []
    predictions: list[dict] = []
    fold_feature_diagnostics: list[dict] = []

    for fold, valid_period, train, valid in _splits(df, spec):
        numeric, categorical, dropped = select_usable_features(
            train, numeric_candidates, categorical_candidates, min_numeric_observations=2
        )
        if not numeric:
            fold_feature_diagnostics.append({
                "fold": int(fold), "period": str(pd.Timestamp(valid_period).date()),
                "active": [], "dropped": dropped, "status": "skipped_no_numeric_features",
                "eval_rows": int(len(valid)),
            })
            continue

        X_train = train[numeric + categorical]
        y_train = train[spec.target_column]
        X_valid = valid[numeric + categorical]
        y_valid = valid[spec.target_column]

        fold_feature_diagnostics.append({
            "fold": int(fold), "period": str(pd.Timestamp(valid_period).date()),
            "active": numeric + categorical, "dropped": dropped, "status": "trained",
            "train_rows": int(len(train)), "eval_rows": int(len(valid)),
        })

        model_predictions: dict[str, np.ndarray] = {
            "baseline_last_value": valid[spec.lag1_column].to_numpy(dtype=float),
            "baseline_seasonal": valid[spec.lag4_column].to_numpy(dtype=float),
        }
        for name, model in _make_models(numeric, categorical).items():
            model.fit(X_train, y_train)
            model_predictions[name] = model.predict(X_valid)

        for name, pred in model_predictions.items():
            metric = regression_metrics(y_valid.to_numpy(dtype=float), pred)
            fold_metric_rows.append({
                "fold": int(fold), "period": str(pd.Timestamp(valid_period).date()),
                "model": name, "n_obs": int(len(valid)), **metric,
            })
            for (_, rec), value in zip(valid.iterrows(), pred):
                predictions.append({
                    "company_id": int(rec["company_id"]), "ticker": rec["ticker"],
                    "fold": int(fold), "period": str(pd.Timestamp(valid_period).date()),
                    "model_name": name, "cutoff_at": rec["cutoff_at"],
                    "target_period_end": pd.Timestamp(rec["target_period_end"]).date(),
                    "predicted_value": float(value), "actual_value": float(rec[spec.target_column]),
                })

    fold_df = pd.DataFrame(fold_metric_rows)
    prediction_df = pd.DataFrame(predictions)
    if fold_df.empty or prediction_df.empty:
        raise RuntimeError(
            f"Nie udało się zbudować walk-forward OOF dla targetu {spec.key}. "
            "Sprawdź raport jakości i historię kwartalną."
        )

    counts = prediction_df.groupby("model_name").size()
    if counts.nunique() != 1:
        raise RuntimeError(f"Błąd porównywalności: modele mają różne liczby OOF: {counts.to_dict()}")
    if int(counts.iloc[0]) < min_common_eval_rows:
        raise RuntimeError(
            f"Po walidacji zostało tylko {int(counts.iloc[0])} wspólnych predykcji OOF; "
            f"minimum to {min_common_eval_rows}."
        )

    summary = summary_from_oof(prediction_df)
    champion = str(summary.iloc[0]["model"])

    known = _applicable(df, spec)
    known = known[known[spec.target_column].notna()].copy()
    final_numeric, final_categorical, final_dropped = select_usable_features(
        known, numeric_candidates, categorical_candidates, min_numeric_observations=2
    )
    if not final_numeric:
        raise RuntimeError("Po filtracji jakościowej nie pozostały żadne cechy liczbowe.")
    final_models = _make_models(final_numeric, final_categorical)

    artifact_dir = Path(get_settings().model_artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    with get_engine().begin() as conn:
        exp_id, dataset_id, version_code = _create_training_context(
            conn, applicable, len(final_numeric + final_categorical), spec
        )
        run_ids: dict[str, int] = {}

        for row in summary.to_dict("records"):
            name = row["model"]
            if name in final_models:
                model = final_models[name]
                model.fit(known[final_numeric + final_categorical], known[spec.target_column])
                artifact = artifact_dir / f"{version_code}_{name}.joblib"
                joblib.dump({
                    "model": model, "numeric": final_numeric, "categorical": final_categorical,
                    "dropped_features": final_dropped, "target_code": spec.target_code,
                    "target_key": spec.key, "dataset_version": version_code,
                }, artifact)
                artifact_uri = str(artifact)
            else:
                artifact_uri = "baseline://no-artifact"

            metrics = {
                "mae": row["mae"], "rmse": row["rmse"], "medae": row["medae"],
                "smape": row["smape"], "wape": row["wape"], "r2": row["r2"],
                "evaluation_observations": row["n_obs"], "walk_forward_folds": row["folds"],
                "evaluation_companies": row["companies"], "evaluation_from": row["evaluation_from"],
                "evaluation_to": row["evaluation_to"], "common_evaluation_sample": True,
                "active_feature_count": len(final_numeric + final_categorical),
                "numeric_feature_count": len(final_numeric), "dropped_feature_count": len(final_dropped),
                "target_key": spec.key,
            }
            run_id = _save_run(
                conn, exp_id=exp_id, dataset_id=dataset_id, spec=spec, model_name=name,
                metrics=metrics, train_from=known["period_end"].min().date(),
                train_to=known["period_end"].max().date(),
                valid_from=pd.to_datetime(row["evaluation_from"]).date(),
                valid_to=pd.to_datetime(row["evaluation_to"]).date(), artifact_uri=artifact_uri,
                hyperparameters={
                    "active_features": final_numeric + final_categorical,
                    "dropped_features": final_dropped,
                    "dynamic_feature_filtering": True,
                    "common_evaluation_required": [spec.target_column, spec.lag1_column, spec.lag4_column],
                    "target_key": spec.key,
                    "target_label": spec.label_pl,
                    "canonical_target_rule": "NET_INCOME_PARENT else NET_INCOME" if spec.key == "net_income" else None,
                    "mapping_version": "v5.3-data-fix",
                    "feature_scope_version": "v5.5-sector-aware",
                    "target_applicability": spec.applicability,
                },
            )
            run_ids[name] = run_id

        for pred in predictions:
            run_id = run_ids[pred["model_name"]]
            conn.execute(text("""
                INSERT INTO ml.prediction(
                    company_id, training_run_id, dataset_version_id, target_code,
                    target_period_end, cutoff_at, predicted_value, actual_value, absolute_error
                ) VALUES (
                    :company_id, :run_id, :dataset_id, :target_code, :target_period_end,
                    :cutoff_at, :predicted_value, :actual_value, :absolute_error
                )
            """), {
                **pred, "run_id": run_id, "dataset_id": dataset_id, "target_code": spec.target_code,
                "absolute_error": abs(pred["predicted_value"] - pred["actual_value"]),
            })

    out_dir = Path("artifacts/real_data_analysis") / spec.key
    out_dir.mkdir(parents=True, exist_ok=True)
    fold_df.to_csv(out_dir / "fold_metrics.csv", index=False)
    summary.to_csv(out_dir / "model_comparison.csv", index=False)
    prediction_df.to_csv(out_dir / "oof_predictions_common_sample.csv", index=False)
    pd.DataFrame(fold_feature_diagnostics).to_json(
        out_dir / "feature_diagnostics.json", orient="records", indent=2, force_ascii=False
    )

    return {
        "dataset_version": version_code,
        "target_key": spec.key,
        "target": spec.target_code,
        "target_label": spec.label_pl,
        "rows": int(len(applicable)),
        "companies": int(applicable["ticker"].nunique()),
        "periods": int(applicable["period_end"].nunique()),
        "known_targets": known_target_rows,
        "raw_common_evaluation_rows": raw_common_rows,
        "raw_common_evaluation_periods": raw_common_periods,
        "common_evaluation_rows": int(counts.iloc[0]),
        "champion": champion,
        "features": final_numeric + final_categorical,
        "dropped_features": final_dropped,
        "fold_feature_diagnostics": fold_feature_diagnostics,
        "models": summary.replace({np.nan: None}).to_dict("records"),
        "warning": (
            "Bankier/Notoria i Yahoo są źródłami agregacyjnymi prototypu. Finalne wartości i daty publikacji "
            "należy zweryfikować z raportami emitenta/ESPI/ESEF przed raportowaniem wyników pracy."
        ),
    }
