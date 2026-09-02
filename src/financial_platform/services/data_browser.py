from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text

from financial_platform.db.session import get_engine
from financial_platform.services.model_dataset import build_dataset_from_db


DATASETS: dict[str, dict[str, Any]] = {
    "market": {
        "label": "Notowania dzienne",
        "description": "Dane OHLCV spółek pobrane z rynku. Jeden wiersz odpowiada jednej sesji giełdowej.",
        "date_field": "trade_date",
        "default_sort": "trade_date",
        "columns": [
            "ticker", "company", "trade_date", "open", "high", "low", "close",
            "adjusted_close", "volume", "available_at",
        ],
    },
    "fundamentals": {
        "label": "Dane fundamentalne",
        "description": "Kwartalne fakty finansowe po mapowaniu do kanonicznych konceptów i wersjonowaniu.",
        "date_field": "period_end",
        "default_sort": "period_end",
        "columns": [
            "ticker", "company", "sector", "concept_code", "concept_name", "value", "unit",
            "period_start", "period_end", "period_type", "publication_date", "available_at",
            "source_label", "source_concept", "revision_no", "is_current",
        ],
    },
    "macro": {
        "label": "Dane makroekonomiczne",
        "description": "Serie makro i walutowe używane do wzbogacenia obserwacji point-in-time.",
        "date_field": "observation_date",
        "default_sort": "observation_date",
        "columns": [
            "series_code", "series_name", "observation_date", "value", "unit", "frequency",
            "source_code", "publication_date", "available_at",
        ],
    },
    "panel": {
        "label": "Dataset modelowy",
        "description": "Panel spółka × kwartał po point-in-time join i feature engineering, bez losowego mieszania czasu.",
        "date_field": "period_end",
        "default_sort": "period_end",
        "columns": [
            "ticker", "sector", "period_end", "cutoff_at", "NET_INCOME_CANONICAL", "REVENUE",
            "target_net_income", "target_revenue", "net_income_lag1", "net_income_lag4", "net_income_yoy",
            "revenue_lag1", "revenue_lag4", "revenue_yoy", "return_20d", "return_60d",
            "volatility_20d", "volume_ratio_20d", "fx_eurpln", "fx_usdpln", "fx_chfpln",
            "net_income_source", "target_source_concept",
        ],
    },
}


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.integer):
        return int(value)
    if pd.isna(value):
        return None
    return value


def _clean_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: _clean_value(v) for k, v in row.items()} for row in rows]


def get_browser_catalog() -> dict[str, Any]:
    with get_engine().connect() as conn:
        tickers = conn.execute(text("""
            SELECT c.ticker, c.name, COALESCE(s.name, '—') AS sector
            FROM core.company c
            LEFT JOIN core.sector s ON s.id=c.sector_id
            WHERE EXISTS (SELECT 1 FROM core.daily_price dp WHERE dp.company_id=c.id)
               OR EXISTS (SELECT 1 FROM core.financial_fact ff WHERE ff.company_id=c.id AND ff.is_current=TRUE)
            ORDER BY c.ticker
        """)).mappings().all()
        concepts = conn.execute(text("""
            SELECT fc.code, fc.name_pl AS name, fc.applicable_to
            FROM core.financial_concept fc
            WHERE EXISTS (
                SELECT 1 FROM core.financial_fact ff
                WHERE ff.financial_concept_id=fc.id AND ff.is_current=TRUE
            )
            ORDER BY fc.code
        """)).mappings().all()
        macro_series = conn.execute(text("""
            SELECT code, name, frequency, source_code
            FROM core.macro_series
            WHERE EXISTS (SELECT 1 FROM core.macro_observation mo WHERE mo.macro_series_id=core.macro_series.id)
            ORDER BY code
        """)).mappings().all()

    return {
        "datasets": [{"code": code, **meta} for code, meta in DATASETS.items()],
        "tickers": [dict(r) for r in tickers],
        "concepts": [dict(r) for r in concepts],
        "macro_series": [dict(r) for r in macro_series],
        "limits": {"max_page_size": 200, "max_export_rows": 5000},
    }


def _sql_browse(
    dataset: str,
    *,
    page: int,
    page_size: int,
    sort: str | None,
    order: str,
    ticker: str | None,
    concept: str | None,
    series: str | None,
    date_from: date | None,
    date_to: date | None,
    search: str | None,
    include_history: bool,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    where: list[str] = []

    if dataset == "market":
        select_sql = """
            SELECT c.ticker, c.name AS company, dp.trade_date,
                   dp.open::double precision AS open, dp.high::double precision AS high,
                   dp.low::double precision AS low, dp.close::double precision AS close,
                   dp.adjusted_close::double precision AS adjusted_close,
                   dp.volume::double precision AS volume, dp.available_at
            FROM core.daily_price dp
            JOIN core.company c ON c.id=dp.company_id
        """
        count_sql = "FROM core.daily_price dp JOIN core.company c ON c.id=dp.company_id"
        sort_map = {k: k for k in ["ticker", "trade_date", "open", "high", "low", "close", "volume", "available_at"]}
        if ticker:
            where.append("c.ticker=:ticker"); params["ticker"] = ticker.upper()
        if date_from:
            where.append("dp.trade_date>=:date_from"); params["date_from"] = date_from
        if date_to:
            where.append("dp.trade_date<=:date_to"); params["date_to"] = date_to
        if search:
            where.append("(c.ticker ILIKE :search OR c.name ILIKE :search)"); params["search"] = f"%{search}%"

    elif dataset == "fundamentals":
        select_sql = """
            SELECT c.ticker, c.name AS company, COALESCE(s.name,'—') AS sector,
                   fc.code AS concept_code, fc.name_pl AS concept_name,
                   ff.value::double precision AS value, ff.unit,
                   ff.period_start, ff.period_end, ff.period_type,
                   ff.publication_date, ff.available_at, ff.source_label, ff.source_concept,
                   ff.revision_no, ff.is_current
            FROM core.financial_fact ff
            JOIN core.company c ON c.id=ff.company_id
            LEFT JOIN core.sector s ON s.id=c.sector_id
            JOIN core.financial_concept fc ON fc.id=ff.financial_concept_id
        """
        count_sql = """
            FROM core.financial_fact ff
            JOIN core.company c ON c.id=ff.company_id
            LEFT JOIN core.sector s ON s.id=c.sector_id
            JOIN core.financial_concept fc ON fc.id=ff.financial_concept_id
        """
        sort_map = {
            "ticker": "c.ticker", "period_end": "ff.period_end", "concept_code": "fc.code",
            "value": "ff.value", "publication_date": "ff.publication_date", "available_at": "ff.available_at",
            "revision_no": "ff.revision_no",
        }
        if not include_history:
            where.append("ff.is_current=TRUE")
        if ticker:
            where.append("c.ticker=:ticker"); params["ticker"] = ticker.upper()
        if concept:
            where.append("fc.code=:concept"); params["concept"] = concept
        if date_from:
            where.append("ff.period_end>=:date_from"); params["date_from"] = date_from
        if date_to:
            where.append("ff.period_end<=:date_to"); params["date_to"] = date_to
        if search:
            where.append("(c.ticker ILIKE :search OR c.name ILIKE :search OR fc.code ILIKE :search OR COALESCE(ff.source_label,'') ILIKE :search OR COALESCE(ff.source_concept,'') ILIKE :search)")
            params["search"] = f"%{search}%"

    elif dataset == "macro":
        select_sql = """
            SELECT ms.code AS series_code, ms.name AS series_name, mo.observation_date,
                   mo.value::double precision AS value, ms.unit, ms.frequency, ms.source_code,
                   mo.publication_date, mo.available_at
            FROM core.macro_observation mo
            JOIN core.macro_series ms ON ms.id=mo.macro_series_id
        """
        count_sql = "FROM core.macro_observation mo JOIN core.macro_series ms ON ms.id=mo.macro_series_id"
        sort_map = {"series_code": "ms.code", "observation_date": "mo.observation_date", "value": "mo.value", "available_at": "mo.available_at"}
        if series:
            where.append("ms.code=:series"); params["series"] = series
        if date_from:
            where.append("mo.observation_date>=:date_from"); params["date_from"] = date_from
        if date_to:
            where.append("mo.observation_date<=:date_to"); params["date_to"] = date_to
        if search:
            where.append("(ms.code ILIKE :search OR ms.name ILIKE :search OR ms.source_code ILIKE :search)"); params["search"] = f"%{search}%"
    else:
        raise ValueError(f"Unsupported SQL dataset: {dataset}")

    where_sql = f" WHERE {' AND '.join(where)}" if where else ""
    chosen_sort = sort if sort in sort_map else DATASETS[dataset]["default_sort"]
    sort_sql = sort_map[chosen_sort]
    order_sql = "ASC" if order.lower() == "asc" else "DESC"
    offset = (page - 1) * page_size

    with get_engine().connect() as conn:
        total = conn.execute(text(f"SELECT count(*) {count_sql}{where_sql}"), params).scalar() or 0
        rows = conn.execute(
            text(f"{select_sql}{where_sql} ORDER BY {sort_sql} {order_sql}, 1 ASC LIMIT :limit OFFSET :offset"),
            {**params, "limit": page_size, "offset": offset},
        ).mappings().all()

    return {
        "dataset": dataset,
        "label": DATASETS[dataset]["label"],
        "description": DATASETS[dataset]["description"],
        "columns": DATASETS[dataset]["columns"],
        "rows": _clean_rows([dict(r) for r in rows]),
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "pages": max(1, int(np.ceil(total / page_size))) if total else 1,
        "sort": chosen_sort,
        "order": order_sql.lower(),
    }


def _panel_browse(
    *,
    page: int,
    page_size: int,
    sort: str | None,
    order: str,
    ticker: str | None,
    date_from: date | None,
    date_to: date | None,
    search: str | None,
    has_target: bool,
) -> dict[str, Any]:
    df = build_dataset_from_db()
    columns = [c for c in DATASETS["panel"]["columns"] if c in df.columns]
    if df.empty:
        return {"dataset": "panel", "label": DATASETS["panel"]["label"], "description": DATASETS["panel"]["description"], "columns": columns, "rows": [], "total": 0, "page": page, "page_size": page_size, "pages": 1, "sort": sort or "period_end", "order": order}

    work = df.copy()
    if ticker:
        work = work[work["ticker"].astype(str).str.upper() == ticker.upper()]
    if date_from:
        work = work[pd.to_datetime(work["period_end"]).dt.date >= date_from]
    if date_to:
        work = work[pd.to_datetime(work["period_end"]).dt.date <= date_to]
    if has_target and "target_net_income" in work:
        work = work[work["target_net_income"].notna()]
    if search:
        mask = work["ticker"].astype(str).str.contains(search, case=False, na=False)
        if "sector" in work:
            mask = mask | work["sector"].astype(str).str.contains(search, case=False, na=False)
        work = work[mask]

    allowed_sort = set(columns)
    chosen_sort = sort if sort in allowed_sort else "period_end"
    work = work.sort_values(chosen_sort, ascending=order.lower() == "asc", na_position="last")
    total = len(work)
    offset = (page - 1) * page_size
    page_df = work.iloc[offset: offset + page_size][columns]
    rows = _clean_rows(page_df.to_dict(orient="records"))
    return {
        "dataset": "panel",
        "label": DATASETS["panel"]["label"],
        "description": DATASETS["panel"]["description"],
        "columns": columns,
        "rows": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, int(np.ceil(total / page_size))) if total else 1,
        "sort": chosen_sort,
        "order": order.lower(),
    }


def browse_data(
    dataset: str,
    *,
    page: int = 1,
    page_size: int = 50,
    sort: str | None = None,
    order: str = "desc",
    ticker: str | None = None,
    concept: str | None = None,
    series: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    include_history: bool = False,
    has_target: bool = False,
) -> dict[str, Any]:
    if dataset not in DATASETS:
        raise ValueError(f"Unknown dataset: {dataset}")
    if dataset == "panel":
        return _panel_browse(
            page=page, page_size=page_size, sort=sort, order=order, ticker=ticker,
            date_from=date_from, date_to=date_to, search=search, has_target=has_target,
        )
    return _sql_browse(
        dataset, page=page, page_size=page_size, sort=sort, order=order, ticker=ticker,
        concept=concept, series=series, date_from=date_from, date_to=date_to, search=search,
        include_history=include_history,
    )
