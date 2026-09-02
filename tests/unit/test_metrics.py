from financial_platform.evaluation.metrics import regression_metrics

def test_metrics_zero_error():
    m=regression_metrics([1,2],[1,2])
    assert m["mae"] == 0
    assert m["rmse"] == 0
