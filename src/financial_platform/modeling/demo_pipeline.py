from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
from financial_platform.datasets.point_in_time import assert_point_in_time
from financial_platform.modeling.baselines import last_value_baseline, seasonal_yoy_baseline
from financial_platform.modeling.train import walk_forward
from financial_platform.evaluation.metrics import regression_metrics

ROOT = Path(__file__).resolve().parents[3]

def run_demo(data_path: Path | None = None) -> dict:
    path = data_path or ROOT / "data" / "demo" / "panel_demo.csv"
    df = pd.read_csv(path)
    for c in ["cutoff_at", "fundamental_available_at", "market_available_at", "macro_available_at"]:
        df[c] = pd.to_datetime(df[c], utc=True)
    assert_point_in_time(df)
    df = df.sort_values(["ticker", "period_index"]).copy()
    base_last = df.groupby("ticker")["target_net_income"].shift(1)
    base_yoy = df.groupby("ticker")["target_net_income"].shift(4)
    mask1 = base_last.notna()
    mask4 = base_yoy.notna()
    result = {
        "NOTE": "DEMO FIXTURE ONLY - not a thesis research result",
        "baseline_last": regression_metrics(df.loc[mask1, "target_net_income"], base_last[mask1]),
        "baseline_yoy": regression_metrics(df.loc[mask4, "target_net_income"], base_yoy[mask4]),
    }
    numeric = ["net_income_lag1", "net_income_lag4", "return_60d", "fx_eurpln"]
    categorical = ["ticker", "sector"]
    for kind in ["ridge", "histgb"]:
        folds = walk_forward(df.dropna(subset=["target_net_income"]), "target_net_income", numeric, categorical, kind, min_train_periods=8)
        result[kind] = [{"fold": f.fold, "valid_period": f.valid_period, **f.metrics} for f in folds]
    return result

if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))
