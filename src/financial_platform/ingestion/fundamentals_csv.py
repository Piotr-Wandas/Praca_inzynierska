from __future__ import annotations
from pathlib import Path
import pandas as pd

REQUIRED = {"ticker", "concept_code", "value", "unit", "period_end", "publication_date", "available_at"}

def load_fundamentals_csv(path: str | Path) -> pd.DataFrame:
    """Prototype structured importer. Research pipeline will later support ESEF/iXBRL adapters."""
    df = pd.read_csv(path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    for col in ["period_end", "publication_date", "available_at"]:
        df[col] = pd.to_datetime(df[col], utc=True)
    return df
