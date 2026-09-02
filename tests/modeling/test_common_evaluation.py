import pandas as pd

from financial_platform.modeling.common_evaluation import common_eval_mask, summary_from_oof


def test_common_eval_requires_target_lag1_and_lag4():
    frame = pd.DataFrame({
        "target_net_income": [10.0, 20.0, 30.0],
        "net_income_lag1": [9.0, 19.0, 29.0],
        "net_income_lag4": [None, 15.0, 25.0],
    })
    assert common_eval_mask(frame).tolist() == [False, True, True]


def test_summary_uses_same_oof_counts_per_model():
    rows = []
    for model, predictions in {
        "baseline_seasonal": [10.0, 20.0, 30.0],
        "ridge": [11.0, 19.0, 31.0],
    }.items():
        for i, (actual, predicted) in enumerate(zip([12.0, 18.0, 33.0], predictions), start=1):
            rows.append({
                "model_name": model,
                "actual_value": actual,
                "predicted_value": predicted,
                "fold": i,
                "ticker": "AAA",
                "target_period_end": ["2024-03-31", "2024-06-30", "2024-09-30"][i-1],
            })
    result = summary_from_oof(pd.DataFrame(rows))
    assert set(result["n_obs"]) == {3}
    assert set(result["folds"]) == {3}


def test_common_eval_is_target_aware_for_revenue():
    frame = pd.DataFrame({
        "target_revenue": [100.0, 110.0, 120.0],
        "revenue_lag1": [90.0, 100.0, 110.0],
        "revenue_lag4": [None, 80.0, 90.0],
        "is_financial": [False, False, True],
    })
    assert common_eval_mask(frame, "revenue").tolist() == [False, True, False]
