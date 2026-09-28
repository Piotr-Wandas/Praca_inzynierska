from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import text

from financial_platform.db.session import get_engine


def _financial_panel() -> pd.DataFrame:
    sql = text("""
        SELECT c.id AS company_id, c.ticker, s.name AS sector,
               COALESCE(s.is_financial, FALSE) AS is_financial,
               ff.period_end, ff.available_at,
               fc.code AS concept_code, ff.value::double precision AS value
        FROM core.financial_fact ff
        JOIN core.company c ON c.id = ff.company_id
        LEFT JOIN core.sector s ON s.id = c.sector_id
        JOIN core.financial_concept fc ON fc.id = ff.financial_concept_id
        WHERE ff.is_current = TRUE AND ff.period_type = 'quarter'
        ORDER BY c.ticker, ff.period_end, ff.available_at
    """)
    with get_engine().connect() as conn:
        facts = pd.read_sql(sql, conn)
    if facts.empty:
        return facts
    facts["period_end"] = pd.to_datetime(facts["period_end"])
    facts["available_at"] = pd.to_datetime(facts["available_at"], utc=True)
    facts = facts.sort_values("available_at").drop_duplicates(
        ["company_id", "concept_code", "period_end"], keep="last"
    )
    values = facts.pivot_table(
        index=["company_id", "ticker", "sector", "is_financial", "period_end"],
        columns="concept_code", values="value", aggfunc="last"
    ).reset_index()
    availability = facts.groupby(
        ["company_id", "ticker", "sector", "is_financial", "period_end"], as_index=False
    )["available_at"].max().rename(columns={"available_at": "cutoff_at"})
    return values.merge(
        availability,
        on=["company_id", "ticker", "sector", "is_financial", "period_end"], how="left"
    )


def _market_features() -> pd.DataFrame:
    sql = text("""
        SELECT dp.company_id, dp.trade_date, dp.close::double precision AS close,
               dp.volume::double precision AS volume, dp.available_at
        FROM core.daily_price dp
        ORDER BY dp.company_id, dp.trade_date
    """)
    with get_engine().connect() as conn:
        df = pd.read_sql(sql, conn)
    if df.empty:
        return df
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["available_at"] = pd.to_datetime(df["available_at"], utc=True)
    g = df.groupby("company_id", group_keys=False)
    df["return_20d"] = g["close"].pct_change(20)
    df["return_60d"] = g["close"].pct_change(60)
    daily_ret = g["close"].pct_change()
    df["volatility_20d"] = daily_ret.groupby(df["company_id"]).transform(
        lambda s: s.rolling(20, min_periods=10).std() * np.sqrt(252)
    )
    avg_volume = g["volume"].transform(lambda s: s.rolling(20, min_periods=5).mean())
    df["volume_ratio_20d"] = df["volume"] / avg_volume.replace(0, np.nan)
    return df[["company_id", "available_at", "return_20d", "return_60d", "volatility_20d", "volume_ratio_20d"]]


def _macro_series(code: str, output_name: str) -> pd.DataFrame:
    sql = text("""
        SELECT mo.available_at, mo.value::double precision AS value
        FROM core.macro_observation mo
        JOIN core.macro_series ms ON ms.id = mo.macro_series_id
        WHERE ms.code = :code
        ORDER BY mo.available_at
    """)
    with get_engine().connect() as conn:
        df = pd.read_sql(sql, conn, params={"code": code})
    if df.empty:
        return df
    df["available_at"] = pd.to_datetime(df["available_at"], utc=True)
    return df.rename(columns={"value": output_name})


def _add_lags(panel: pd.DataFrame, source: str, prefix: str) -> None:
    if source not in panel.columns:
        return
    g = panel.groupby("ticker")[source]
    panel[f"{prefix}_lag1"] = g.shift(1)
    panel[f"{prefix}_lag4"] = g.shift(4)
    denominator = panel[f"{prefix}_lag4"].abs().replace(0, np.nan)
    panel[f"{prefix}_yoy"] = (panel[source] - panel[f"{prefix}_lag4"]) / denominator


def build_dataset_from_db() -> pd.DataFrame:
    """Buduje panel point-in-time: spółka × kwartał.

    v5.3 stosuje trzy jawne targety: kanoniczny zysk netto t+1 dla całego panelu,
    przychody t+1 dla spółek niefinansowych oraz wynik odsetkowy t+1 dla banków.
    Kanoniczny zysk netto preferuje NET_INCOME_PARENT, a przy jego braku NET_INCOME.
    """
    panel = _financial_panel()
    if panel.empty:
        return panel
    panel = panel.sort_values(["ticker", "period_end"]).reset_index(drop=True)

    parent = panel["NET_INCOME_PARENT"] if "NET_INCOME_PARENT" in panel.columns else pd.Series(np.nan, index=panel.index)
    generic = panel["NET_INCOME"] if "NET_INCOME" in panel.columns else pd.Series(np.nan, index=panel.index)
    panel["NET_INCOME_CANONICAL"] = parent.combine_first(generic)
    panel["net_income_source"] = np.select(
        [parent.notna(), generic.notna()], ["NET_INCOME_PARENT", "NET_INCOME"], default=None
    )

    if panel["NET_INCOME_CANONICAL"].notna().sum() == 0:
        raise RuntimeError("Brak danych NET_INCOME_PARENT/NET_INCOME w bazie.")

    for source, prefix in [
        ("NET_INCOME_CANONICAL", "net_income"),
        ("REVENUE", "revenue"),
        ("OPERATING_PROFIT", "operating_profit"),
        ("TOTAL_ASSETS", "total_assets"),
        ("EQUITY", "equity"),
        ("NET_INTEREST_INCOME", "net_interest_income"),
        ("NET_FEE_INCOME", "net_fee_income"),
    ]:
        _add_lags(panel, source, prefix)

    # Alias tylko dla zgodności ze starszym dashboardem/artefaktami v5.1.
    for suffix in ("lag1", "lag4", "yoy"):
        src = f"net_income_{suffix}"
        if src in panel:
            panel[f"net_income_parent_{suffix}"] = panel[src]

    g = panel.groupby("ticker")
    panel["target_net_income"] = g["NET_INCOME_CANONICAL"].shift(-1)
    panel["target_revenue"] = g["REVENUE"].shift(-1) if "REVENUE" in panel.columns else np.nan
    panel["target_net_interest_income"] = (
        g["NET_INTEREST_INCOME"].shift(-1) if "NET_INTEREST_INCOME" in panel.columns else np.nan
    )
    # Targety sektorowe są jawnie ograniczone do właściwych typów spółek.
    panel.loc[panel["is_financial"].astype(bool), "target_revenue"] = np.nan
    panel.loc[~panel["is_financial"].astype(bool), "target_net_interest_income"] = np.nan
    panel["target_period_end"] = g["period_end"].shift(-1)
    panel["target_source_concept"] = g["net_income_source"].shift(-1)

    market = _market_features()
    if not market.empty:
        parts = []
        for company_id, group in panel.groupby("company_id"):
            right = market[market["company_id"] == company_id].sort_values("available_at")
            left = group.sort_values("cutoff_at")
            if right.empty:
                parts.append(left)
            else:
                parts.append(pd.merge_asof(
                    left, right.drop(columns=["company_id"]),
                    left_on="cutoff_at", right_on="available_at",
                    direction="backward", suffixes=("", "_market")
                ))
        panel = pd.concat(parts, ignore_index=True)

    for code, out_name in [
        ("FX_EUR_PLN", "fx_eurpln"),
        ("FX_USD_PLN", "fx_usdpln"),
        ("FX_CHF_PLN", "fx_chfpln"),
    ]:
        macro = _macro_series(code, out_name)
        if macro.empty:
            continue
        panel = pd.merge_asof(
            panel.sort_values("cutoff_at"), macro.sort_values("available_at"),
            left_on="cutoff_at", right_on="available_at", direction="backward",
            suffixes=("", f"_{out_name}")
        )

    panel["quarter"] = panel["period_end"].dt.quarter.astype(str)
    return panel.sort_values(["period_end", "ticker"]).reset_index(drop=True)
