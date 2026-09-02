from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from financial_platform.evaluation.metrics import regression_metrics

@dataclass
class FoldResult:
    model: str
    fold: int
    train_end: int
    valid_period: int
    metrics: dict[str, float]

def make_model(kind: str, numeric: list[str], categorical: list[str]) -> Pipeline:
    numeric_pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    pre = ColumnTransformer([("num", numeric_pipe, numeric), ("cat", categorical_pipe, categorical)])
    if kind == "ridge":
        estimator = Ridge(alpha=1.0)
    elif kind == "histgb":
        estimator = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.06, max_iter=150, random_state=42)
    else:
        raise ValueError(kind)
    return Pipeline([("pre", pre), ("model", estimator)])

def walk_forward(df: pd.DataFrame, target: str, numeric: list[str], categorical: list[str], kind: str, min_train_periods: int = 8) -> list[FoldResult]:
    work = df.sort_values("period_index").copy()
    periods = sorted(work["period_index"].unique())
    results: list[FoldResult] = []
    Xcols = numeric + categorical
    for fold, valid_period in enumerate(periods[min_train_periods:], start=1):
        train = work[work["period_index"] < valid_period]
        valid = work[work["period_index"] == valid_period]
        if train.empty or valid.empty:
            continue
        model = make_model(kind, numeric, categorical)
        model.fit(train[Xcols], train[target])
        pred = model.predict(valid[Xcols])
        results.append(FoldResult(kind, fold, int(train["period_index"].max()), int(valid_period), regression_metrics(valid[target], pred)))
    return results
