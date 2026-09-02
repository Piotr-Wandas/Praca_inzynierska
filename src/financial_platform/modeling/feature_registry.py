from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    scope: str = "all"  # all | financial | non_financial
    group: str = "global"
    label_pl: str | None = None


FEATURE_SPECS: dict[str, FeatureSpec] = {
    # Global financial history
    "net_income_lag1": FeatureSpec("net_income_lag1", "all", "wyniki", "Zysk netto t-1"),
    "net_income_lag4": FeatureSpec("net_income_lag4", "all", "wyniki", "Zysk netto t-4"),
    "net_income_yoy": FeatureSpec("net_income_yoy", "all", "wyniki", "Zmiana zysku netto r/r"),
    "total_assets_lag1": FeatureSpec("total_assets_lag1", "all", "bilans", "Aktywa t-1"),
    "equity_lag1": FeatureSpec("equity_lag1", "all", "bilans", "Kapitał własny t-1"),

    # Non-financial company features
    "revenue_lag1": FeatureSpec("revenue_lag1", "non_financial", "niefinansowe", "Przychody t-1"),
    "revenue_lag4": FeatureSpec("revenue_lag4", "non_financial", "niefinansowe", "Przychody t-4"),
    "revenue_yoy": FeatureSpec("revenue_yoy", "non_financial", "niefinansowe", "Zmiana przychodów r/r"),
    "operating_profit_lag1": FeatureSpec("operating_profit_lag1", "non_financial", "niefinansowe", "Wynik operacyjny t-1"),

    # Financial-sector features
    "net_interest_income_lag1": FeatureSpec("net_interest_income_lag1", "financial", "banki", "Wynik odsetkowy t-1"),
    "net_interest_income_lag4": FeatureSpec("net_interest_income_lag4", "financial", "banki", "Wynik odsetkowy t-4"),
    "net_interest_income_yoy": FeatureSpec("net_interest_income_yoy", "financial", "banki", "Zmiana wyniku odsetkowego r/r"),
    "net_fee_income_lag1": FeatureSpec("net_fee_income_lag1", "financial", "banki", "Wynik prowizyjny t-1"),
    "net_fee_income_lag4": FeatureSpec("net_fee_income_lag4", "financial", "banki", "Wynik prowizyjny t-4"),
    "net_fee_income_yoy": FeatureSpec("net_fee_income_yoy", "financial", "banki", "Zmiana wyniku prowizyjnego r/r"),

    # Market features
    "return_20d": FeatureSpec("return_20d", "all", "rynek", "Stopa zwrotu 20 sesji"),
    "return_60d": FeatureSpec("return_60d", "all", "rynek", "Stopa zwrotu 60 sesji"),
    "volatility_20d": FeatureSpec("volatility_20d", "all", "rynek", "Zmienność 20 sesji"),
    "volume_ratio_20d": FeatureSpec("volume_ratio_20d", "all", "rynek", "Relatywny wolumen 20 sesji"),

    # Macro features
    "fx_eurpln": FeatureSpec("fx_eurpln", "all", "makro", "EUR/PLN"),
    "fx_usdpln": FeatureSpec("fx_usdpln", "all", "makro", "USD/PLN"),
    "fx_chfpln": FeatureSpec("fx_chfpln", "all", "makro", "CHF/PLN"),

    # Categorical
    "ticker": FeatureSpec("ticker", "all", "kategoryczne", "Spółka"),
    "sector": FeatureSpec("sector", "all", "kategoryczne", "Sektor"),
    "quarter": FeatureSpec("quarter", "all", "kategoryczne", "Kwartał"),
    "net_income_source": FeatureSpec("net_income_source", "all", "kategoryczne", "Źródło targetu zysku netto"),
}


def feature_spec(name: str) -> FeatureSpec:
    return FEATURE_SPECS.get(name, FeatureSpec(name=name))


def applicable_mask(frame: pd.DataFrame, scope: str) -> pd.Series:
    if len(frame) == 0:
        return pd.Series(False, index=frame.index, dtype=bool)
    if scope == "financial" and "is_financial" in frame.columns:
        return frame["is_financial"].astype(bool)
    if scope == "non_financial" and "is_financial" in frame.columns:
        return ~frame["is_financial"].astype(bool)
    return pd.Series(True, index=frame.index, dtype=bool)


def feature_candidates_for_target(
    target_applicability: str,
    numeric_candidates: list[str],
    categorical_candidates: list[str],
) -> tuple[list[str], list[str]]:
    """Zwraca cechy semantycznie właściwe dla danego targetu.

    Dla globalnego targetu zysku netto pozostają tylko cechy globalne. Cechy
    sektorowe nie są medianowo imputowane do spółek, dla których nie mają sensu.
    Dla targetów sektorowych dopuszczone są cechy globalne + właściwy sektor.
    """
    if target_applicability == "financial":
        allowed_scopes = {"all", "financial"}
    elif target_applicability == "non_financial":
        allowed_scopes = {"all", "non_financial"}
    else:
        allowed_scopes = {"all"}

    numeric = [c for c in numeric_candidates if feature_spec(c).scope in allowed_scopes]
    categorical = [c for c in categorical_candidates if feature_spec(c).scope in allowed_scopes]
    return numeric, categorical


def scoped_feature_coverage(frame: pd.DataFrame, columns: list[str]) -> list[dict]:
    """Oblicza kompletność cech względem populacji, dla której cecha ma zastosowanie."""
    rows: list[dict] = []
    total = len(frame)
    for col in columns:
        spec = feature_spec(col)
        mask = applicable_mask(frame, spec.scope)
        eligible_rows = int(mask.sum())
        eligible_companies = int(frame.loc[mask, "ticker"].nunique()) if eligible_rows and "ticker" in frame.columns else 0
        if col not in frame.columns:
            rows.append({
                "feature": col, "label": spec.label_pl or col, "scope": spec.scope, "group": spec.group,
                "observed": 0, "missing": eligible_rows, "eligible_rows": eligible_rows,
                "eligible_companies": eligible_companies, "coverage": 0.0, "global_coverage": 0.0,
            })
            continue
        observed = int(frame.loc[mask, col].notna().sum())
        coverage = observed / eligible_rows if eligible_rows else 0.0
        global_observed = int(frame[col].notna().sum())
        global_coverage = global_observed / total if total else 0.0
        rows.append({
            "feature": col, "label": spec.label_pl or col, "scope": spec.scope, "group": spec.group,
            "observed": observed, "missing": int(eligible_rows - observed),
            "eligible_rows": eligible_rows, "eligible_companies": eligible_companies,
            "coverage": round(coverage, 4), "global_coverage": round(global_coverage, 4),
        })
    return rows
