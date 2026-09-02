from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from financial_platform.features.feature_builder import build_panel_features
from financial_platform.modeling.experiment_runner import ExperimentConfig, run_experiment, save_experiment_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Semester-II reproducible model analysis")
    parser.add_argument("--input", default="data/demo/panel_demo.csv")
    parser.add_argument("--output", default="artifacts/semester2_analysis")
    parser.add_argument("--mlflow", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df = build_panel_features(df)

    numeric = [
        c for c in [
            "net_income_lag1",
            "net_income_lag4",
            "return_60d",
            "fx_eurpln",
        ] if c in df.columns
    ]
    categorical = [c for c in ["ticker", "sector", "quarter"] if c in df.columns]

    folds, summary = run_experiment(
        df,
        numeric_features=numeric,
        categorical_features=categorical,
        config=ExperimentConfig(min_train_periods=8),
        enable_mlflow=args.mlflow,
    )
    save_experiment_outputs(folds, summary, Path(args.output))

    print("\n=== MODEL COMPARISON ===")
    print(summary.to_string(index=False))
    print(f"\nOutputs saved in: {args.output}")
    print("NOTE: data/demo is synthetic and must not be reported as thesis results.")


if __name__ == "__main__":
    main()
