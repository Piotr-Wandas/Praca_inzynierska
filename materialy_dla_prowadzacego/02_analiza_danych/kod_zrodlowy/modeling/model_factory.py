from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _preprocessor(numeric: list[str], categorical: list[str], scale_numeric: bool) -> ColumnTransformer:
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipe = Pipeline(numeric_steps)
    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [("num", numeric_pipe, numeric), ("cat", categorical_pipe, categorical)],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def make_ridge(numeric: list[str], categorical: list[str]) -> Pipeline:
    return Pipeline([
        ("prep", _preprocessor(numeric, categorical, scale_numeric=True)),
        ("model", Ridge(alpha=1.0)),
    ])


def make_random_forest(numeric: list[str], categorical: list[str]) -> Pipeline:
    return Pipeline([
        ("prep", _preprocessor(numeric, categorical, scale_numeric=False)),
        ("model", RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=3,
            max_features="sqrt",
            random_state=42,
            n_jobs=-1,
        )),
    ])


def make_hist_gradient_boosting(numeric: list[str], categorical: list[str]) -> Pipeline:
    return Pipeline([
        ("prep", _preprocessor(numeric, categorical, scale_numeric=False)),
        ("model", HistGradientBoostingRegressor(
            max_depth=4,
            learning_rate=0.06,
            max_iter=200,
            l2_regularization=0.5,
            random_state=42,
        )),
    ])
