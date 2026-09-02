from financial_platform.evaluation.metrics import regression_metrics


def test_regression_metrics_contains_expected_keys():
    result = regression_metrics([100, 200, 300], [110, 190, 310])
    assert {"mae", "rmse", "medae", "smape", "wape", "r2"}.issubset(result)
    assert result["mae"] > 0
