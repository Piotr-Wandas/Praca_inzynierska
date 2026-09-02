from __future__ import annotations

import numpy as np
import pandas as pd


def normalize_money(value: pd.Series, unit: pd.Series) -> pd.Series:
    """Convert PLN / thousands PLN / millions PLN into PLN."""
    multipliers = {
        "PLN": 1.0,
        "TPLN": 1_000.0,
        "THOUSAND_PLN": 1_000.0,
        "MPLN": 1_000_000.0,
        "MILLION_PLN": 1_000_000.0,
    }
    factor = unit.astype(str).str.upper().map(multipliers)
    if factor.isna().any():
        unknown = sorted(unit[factor.isna()].astype(str).unique().tolist())
        raise ValueError(f"Unknown monetary unit(s): {unknown}")
    return pd.to_numeric(value, errors="coerce") * factor


def signed_log1p(values: pd.Series) -> pd.Series:
    """Stable transform for targets that may be negative or zero."""
    x = pd.to_numeric(values, errors="coerce")
    return np.sign(x) * np.log1p(np.abs(x))


def clean_fundamentals(df: pd.DataFrame) -> pd.DataFrame:
    required = {"ticker", "concept_code", "value", "period_end", "publication_date", "available_at"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing fundamental columns: {sorted(missing)}")
    out = df.copy()
    for c in ["period_end", "publication_date", "available_at"]:
        out[c] = pd.to_datetime(out[c], utc=True, errors="raise")
    if (out["publication_date"].dt.date < out["period_end"].dt.date).any():
        raise ValueError("Publication date before period end")
    if (out["available_at"] < out["publication_date"]).any():
        raise ValueError("available_at before publication_date")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.sort_values(["ticker", "concept_code", "period_end", "available_at"]).reset_index(drop=True)
