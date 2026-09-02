import pandas as pd
from financial_platform.validation.market import validate_ohlcv

def test_valid_ohlcv():
    df = pd.DataFrame({"open":[10],"high":[12],"low":[9],"close":[11],"volume":[100]})
    assert validate_ohlcv(df) == []

def test_invalid_high_is_detected():
    df = pd.DataFrame({"open":[13],"high":[12],"low":[9],"close":[11],"volume":[100]})
    assert validate_ohlcv(df)
