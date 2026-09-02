from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from financial_platform.db.session import get_engine
from financial_platform.services.internet_ingestion import run_full_ingestion
from financial_platform.services.train_from_db import train_models_from_db
from financial_platform.services.data_quality import get_data_quality_report
from financial_platform.services.data_browser import get_browser_catalog, browse_data

app = FastAPI(title="WIG20 Financial Prediction Platform", version="0.6.0")


def _latest_dataset_id(conn, target_code: str | None = "NET_INCOME_CANONICAL"):
    if target_code:
        return conn.execute(text("""
            SELECT dataset_version_id
            FROM ml.training_run
            WHERE status='completed' AND dataset_version_id IS NOT NULL AND target_code=:target_code
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """), {"target_code": target_code}).scalar()
    return conn.execute(text("""
        SELECT dataset_version_id
        FROM ml.training_run
        WHERE status='completed' AND dataset_version_id IS NOT NULL
        ORDER BY created_at DESC, id DESC
        LIMIT 1
    """)).scalar()


@app.get("/api/v1/system/health")
def health():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok", "version": "v6.0", "stage": "review-release", "app_mode": os.getenv("APP_MODE", "development")}
    except Exception as exc:
        return {"status": "degraded", "database": "error", "detail": str(exc)}


@app.get("/api/v1/review/info")
def review_info():
    path = Path(os.getenv("REVIEW_METADATA_PATH", "/app/review/metadata/snapshot.json"))
    snapshot = {"prepared": False}
    try:
        if path.exists():
            snapshot = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        snapshot = {"prepared": False, "error": str(exc)}
    return {
        "release": "v6.0 REVIEW RELEASE",
        "mode": os.getenv("APP_MODE", "development"),
        "snapshot": snapshot,
        "urls": {
            "app": "http://localhost:3000",
            "review": "http://localhost:3000/review",
            "data": "http://localhost:3000/data",
            "browser": "http://localhost:3000/data-browser",
            "models": "http://localhost:3000/models",
            "api_docs": "http://localhost:8000/docs"
        }
    }


@app.get("/api/v1/methodology")
def methodology():
    return {
        "market": "GPW pilot universe / WIG20-oriented",
        "horizon": "t+1 quarter",
        "targets": ["NET_INCOME_CANONICAL", "REVENUE", "NET_INTEREST_INCOME"],
        "target_rule": "NET_INCOME_PARENT preferred, NET_INCOME fallback; sector targets available",
        "mapping": "v5.3 audited Bankier/Notoria source-label mapping",
        "validation": "walk-forward",
        "comparison": "common out-of-fold evaluation sample for every compared model",
        "point_in_time": True,
        "sources": [
            "Bankier.pl (prototype long-history fundamentals)",
            "Yahoo Finance (market + fundamental fallback)",
            "NBP Web API",
            "GUS BDL adapter",
        ],
        "warning": "Bankier/Yahoo are prototype aggregation sources. Final thesis values and filing dates should be verified with issuer/ESPI/ESEF.",
        "disclaimer": "Research and educational prototype; not investment advice.",
    }


@app.get("/api/v1/dashboard/summary")
def dashboard_summary():
    with get_engine().connect() as conn:
        company_count = conn.execute(text("SELECT count(*) FROM core.company")).scalar() or 0
        price_count = conn.execute(text("SELECT count(*) FROM core.daily_price")).scalar() or 0
        fact_count = conn.execute(text("SELECT count(*) FROM core.financial_fact WHERE is_current=TRUE")).scalar() or 0
        macro_count = conn.execute(text("SELECT count(*) FROM core.macro_observation")).scalar() or 0
        last_ingestion = conn.execute(text("""
            SELECT source_name, status, records_received, finished_at
            FROM metadata.ingestion_run ORDER BY started_at DESC LIMIT 1
        """)).mappings().first()
        dataset_id = _latest_dataset_id(conn)
        champion = None
        dataset_version = None
        if dataset_id:
            champion = conn.execute(text("""
                SELECT model_name, metrics, created_at
                FROM ml.training_run
                WHERE status='completed' AND dataset_version_id=:dataset_id AND metrics IS NOT NULL
                ORDER BY NULLIF(metrics->>'mae','')::double precision ASC NULLS LAST, id ASC
                LIMIT 1
            """), {"dataset_id": dataset_id}).mappings().first()
            dataset_version = conn.execute(text("""
                SELECT version_code, row_count, feature_count, created_at
                FROM ml.dataset_version WHERE id=:dataset_id
            """), {"dataset_id": dataset_id}).mappings().first()
    return {
        "companies": company_count,
        "market_rows": price_count,
        "fundamental_rows": fact_count,
        "macro_rows": macro_count,
        "last_ingestion": dict(last_ingestion) if last_ingestion else None,
        "champion": dict(champion) if champion else None,
        "dataset_version": dict(dataset_version) if dataset_version else None,
    }


@app.get("/api/v1/dashboard/data-quality")
def dashboard_data_quality():
    try:
        return get_data_quality_report()
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@app.get("/api/v1/dashboard/companies")
def dashboard_companies():
    with get_engine().connect() as conn:
        rows = conn.execute(text("""
            WITH prices AS (
                SELECT company_id, count(*) AS price_rows, max(trade_date) AS last_price_date
                FROM core.daily_price GROUP BY company_id
            ), facts AS (
                SELECT company_id, count(*) AS fundamental_rows, max(period_end) AS last_report_period
                FROM core.financial_fact WHERE is_current=TRUE GROUP BY company_id
            )
            SELECT c.ticker, c.name, s.name AS sector,
                   COALESCE(p.price_rows, 0) AS price_rows,
                   COALESCE(f.fundamental_rows, 0) AS fundamental_rows,
                   p.last_price_date, f.last_report_period
            FROM core.company c
            LEFT JOIN core.sector s ON s.id=c.sector_id
            LEFT JOIN prices p ON p.company_id=c.id
            LEFT JOIN facts f ON f.company_id=c.id
            ORDER BY c.ticker
        """)).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/v1/dashboard/company/{ticker}")
def dashboard_company(ticker: str):
    ticker = ticker.upper()
    with get_engine().connect() as conn:
        company = conn.execute(text("""
            SELECT c.id, c.ticker, c.name, s.name AS sector
            FROM core.company c LEFT JOIN core.sector s ON s.id=c.sector_id
            WHERE c.ticker=:ticker
        """), {"ticker": ticker}).mappings().first()
        if not company:
            raise HTTPException(404, "Company not found")
        financials = conn.execute(text("""
            SELECT ff.period_end, fc.code AS concept, ff.value::double precision AS value,
                   ff.available_at, ff.source_label, ff.source_concept
            FROM core.financial_fact ff
            JOIN core.financial_concept fc ON fc.id=ff.financial_concept_id
            WHERE ff.company_id=:company_id AND ff.is_current=TRUE
            ORDER BY ff.period_end, fc.code
        """), {"company_id": company["id"]}).mappings().all()
        prices = conn.execute(text("""
            SELECT trade_date, close::double precision AS close, volume::double precision AS volume
            FROM core.daily_price WHERE company_id=:company_id
            ORDER BY trade_date DESC LIMIT 260
        """), {"company_id": company["id"]}).mappings().all()
        dataset_id = _latest_dataset_id(conn)
        predictions = []
        if dataset_id:
            predictions = conn.execute(text("""
                SELECT p.target_period_end, p.predicted_value::double precision AS predicted_value,
                       p.actual_value::double precision AS actual_value,
                       p.absolute_error::double precision AS absolute_error, tr.model_name
                FROM ml.prediction p
                JOIN ml.training_run tr ON tr.id=p.training_run_id
                WHERE p.company_id=:company_id AND p.dataset_version_id=:dataset_id
                ORDER BY p.target_period_end, tr.model_name
            """), {"company_id": company["id"], "dataset_id": dataset_id}).mappings().all()
    return {
        "company": dict(company),
        "financials": [dict(x) for x in financials],
        "prices": [dict(x) for x in reversed(prices)],
        "predictions": [dict(x) for x in predictions],
    }


@app.get("/api/v1/dashboard/models")
def dashboard_models(
    latest: bool = Query(True),
    target_code: str = Query("NET_INCOME_CANONICAL"),
):
    with get_engine().connect() as conn:
        dataset_id = _latest_dataset_id(conn, target_code=target_code) if latest else None
        if latest and dataset_id:
            rows = conn.execute(text("""
                SELECT tr.id, tr.dataset_version_id, dv.version_code AS dataset_version,
                       tr.model_name, tr.target_code, tr.metrics, tr.hyperparameters,
                       tr.train_from, tr.train_to, tr.validation_from, tr.validation_to,
                       tr.created_at, tr.artifact_uri
                FROM ml.training_run tr
                JOIN ml.dataset_version dv ON dv.id=tr.dataset_version_id
                WHERE tr.status='completed' AND tr.dataset_version_id=:dataset_id
                ORDER BY NULLIF(tr.metrics->>'mae','')::double precision ASC NULLS LAST, tr.id
            """), {"dataset_id": dataset_id}).mappings().all()
        else:
            rows = conn.execute(text("""
                SELECT tr.id, tr.dataset_version_id, dv.version_code AS dataset_version,
                       tr.model_name, tr.target_code, tr.metrics, tr.hyperparameters,
                       tr.train_from, tr.train_to, tr.validation_from, tr.validation_to,
                       tr.created_at, tr.artifact_uri
                FROM ml.training_run tr
                LEFT JOIN ml.dataset_version dv ON dv.id=tr.dataset_version_id
                WHERE tr.status='completed' AND tr.target_code=:target_code
                ORDER BY tr.created_at DESC, tr.id DESC
            """), {"target_code": target_code}).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/v1/dashboard/model-diagnostics")
def model_diagnostics(target_code: str = Query("NET_INCOME_CANONICAL")):
    with get_engine().connect() as conn:
        dataset_id = _latest_dataset_id(conn, target_code=target_code)
        if not dataset_id:
            return {"dataset_version": None, "models": [], "by_company": [], "by_period": []}
        version = conn.execute(text("SELECT version_code FROM ml.dataset_version WHERE id=:id"), {"id": dataset_id}).scalar()
        models = conn.execute(text("""
            SELECT tr.model_name, tr.metrics
            FROM ml.training_run tr
            WHERE tr.dataset_version_id=:dataset_id AND tr.status='completed'
            ORDER BY NULLIF(tr.metrics->>'mae','')::double precision ASC NULLS LAST
        """), {"dataset_id": dataset_id}).mappings().all()
        by_company = conn.execute(text("""
            SELECT c.ticker, tr.model_name, count(*) AS observations,
                   avg(p.absolute_error)::double precision AS mae,
                   sqrt(avg(power(p.predicted_value-p.actual_value, 2)))::double precision AS rmse
            FROM ml.prediction p
            JOIN ml.training_run tr ON tr.id=p.training_run_id
            JOIN core.company c ON c.id=p.company_id
            WHERE p.dataset_version_id=:dataset_id AND p.actual_value IS NOT NULL
            GROUP BY c.ticker, tr.model_name
            ORDER BY c.ticker, mae
        """), {"dataset_id": dataset_id}).mappings().all()
        by_period = conn.execute(text("""
            SELECT p.target_period_end, tr.model_name, count(*) AS observations,
                   avg(p.absolute_error)::double precision AS mae
            FROM ml.prediction p
            JOIN ml.training_run tr ON tr.id=p.training_run_id
            WHERE p.dataset_version_id=:dataset_id AND p.actual_value IS NOT NULL
            GROUP BY p.target_period_end, tr.model_name
            ORDER BY p.target_period_end, tr.model_name
        """), {"dataset_id": dataset_id}).mappings().all()
    return {
        "dataset_version": version,
        "models": [dict(r) for r in models],
        "by_company": [dict(r) for r in by_company],
        "by_period": [dict(r) for r in by_period],
    }


@app.get("/api/v1/data-preparation")
def data_preparation_dashboard():
    """Statystyki przygotowania i jakości danych do prezentacji w aplikacji."""
    quality = get_data_quality_report()
    with get_engine().connect() as conn:
        ranges = conn.execute(text("""
            SELECT
              (SELECT min(trade_date) FROM core.daily_price) AS market_from,
              (SELECT max(trade_date) FROM core.daily_price) AS market_to,
              (SELECT min(period_end) FROM core.financial_fact WHERE is_current=TRUE) AS fundamentals_from,
              (SELECT max(period_end) FROM core.financial_fact WHERE is_current=TRUE) AS fundamentals_to,
              (SELECT min(observation_date) FROM core.macro_observation) AS macro_from,
              (SELECT max(observation_date) FROM core.macro_observation) AS macro_to
        """)).mappings().first()

        companies = conn.execute(text("""
            WITH p AS (
              SELECT company_id, count(*) AS market_rows, min(trade_date) AS market_from, max(trade_date) AS market_to
              FROM core.daily_price GROUP BY company_id
            ), f AS (
              SELECT ff.company_id, count(*) AS fundamental_rows, count(DISTINCT ff.period_end) AS fundamental_periods,
                     count(DISTINCT ff.financial_concept_id) AS concepts, min(ff.period_end) AS fundamental_from, max(ff.period_end) AS fundamental_to,
                     count(*) FILTER (WHERE fc.code IN ('NET_INCOME_PARENT','NET_INCOME')) AS net_income_rows,
                     count(*) FILTER (WHERE fc.code='REVENUE') AS revenue_rows
              FROM core.financial_fact ff
              JOIN core.financial_concept fc ON fc.id=ff.financial_concept_id
              WHERE ff.is_current=TRUE
              GROUP BY ff.company_id
            )
            SELECT c.ticker, c.name, COALESCE(s.name,'—') AS sector,
                   COALESCE(p.market_rows,0) AS market_rows, p.market_from, p.market_to,
                   COALESCE(f.fundamental_rows,0) AS fundamental_rows, COALESCE(f.fundamental_periods,0) AS fundamental_periods,
                   COALESCE(f.concepts,0) AS concepts, f.fundamental_from, f.fundamental_to,
                   COALESCE(f.net_income_rows,0) AS net_income_rows, COALESCE(f.revenue_rows,0) AS revenue_rows
            FROM core.company c
            LEFT JOIN core.sector s ON s.id=c.sector_id
            LEFT JOIN p ON p.company_id=c.id
            LEFT JOIN f ON f.company_id=c.id
            WHERE COALESCE(p.market_rows,0) > 0 OR COALESCE(f.fundamental_rows,0) > 0
            ORDER BY c.ticker
        """)).mappings().all()

        quarters = conn.execute(text("""
            SELECT period_end,
                   extract(year from period_end)::int AS year,
                   extract(quarter from period_end)::int AS quarter,
                   count(*) AS facts,
                   count(DISTINCT ff.company_id) AS companies,
                   count(DISTINCT ff.company_id) FILTER (WHERE fc.code IN ('NET_INCOME_PARENT','NET_INCOME')) AS net_income_companies,
                   count(DISTINCT ff.company_id) FILTER (WHERE fc.code='REVENUE') AS revenue_companies
            FROM core.financial_fact ff
            JOIN core.financial_concept fc ON fc.id=ff.financial_concept_id
            WHERE ff.is_current=TRUE
            GROUP BY period_end
            ORDER BY period_end
        """)).mappings().all()

        concepts = conn.execute(text("""
            SELECT fc.code, fc.name_pl, fc.applicable_to, fc.value_type,
                   count(*) AS rows, count(DISTINCT ff.company_id) AS companies, count(DISTINCT ff.period_end) AS periods,
                   min(ff.period_end) AS first_period, max(ff.period_end) AS last_period
            FROM core.financial_concept fc
            JOIN core.financial_fact ff ON ff.financial_concept_id=fc.id AND ff.is_current=TRUE
            GROUP BY fc.id, fc.code, fc.name_pl, fc.applicable_to, fc.value_type
            ORDER BY count(*) DESC, fc.code
        """)).mappings().all()

        macro = conn.execute(text("""
            SELECT ms.code, ms.name, ms.unit, ms.frequency, ms.source_code,
                   count(mo.id) AS rows, min(mo.observation_date) AS first_date, max(mo.observation_date) AS last_date
            FROM core.macro_series ms
            LEFT JOIN core.macro_observation mo ON mo.macro_series_id=ms.id
            GROUP BY ms.id, ms.code, ms.name, ms.unit, ms.frequency, ms.source_code
            ORDER BY ms.code
        """)).mappings().all()

        checks = conn.execute(text("""
            SELECT
              (SELECT count(*) FROM core.daily_price WHERE volume IS NULL) AS market_missing_volume,
              (SELECT count(*) FROM core.financial_fact WHERE is_current=TRUE AND available_at::date = (period_end + 120)) AS proxy_120d_rows,
              (SELECT count(*) FROM staging.financial_mapping_audit WHERE mapped_concept_code IS NULL AND values_observed > 0) AS unmatched_mapping_labels,
              (SELECT count(*) FROM core.financial_fact WHERE is_current=TRUE) AS current_facts,
              (SELECT count(*) FROM core.financial_fact WHERE is_current=FALSE) AS historical_fact_versions
        """)).mappings().first()

    pipeline = [
        {"step": 1, "name": "Pozyskanie", "detail": "Bankier/Notoria, Yahoo Finance, NBP, GUS adapter"},
        {"step": 2, "name": "RAW / staging", "detail": "Audyt etykiet, identyfikacja źródła i wersji"},
        {"step": 3, "name": "Walidacja", "detail": "Typy, daty, OHLCV, jednostki, duplikaty i mapowanie konceptów"},
        {"step": 4, "name": "Core PostgreSQL", "detail": "Notowania, fakty finansowe, makro i wersjonowanie"},
        {"step": 5, "name": "Point-in-time", "detail": "Łączenie wyłącznie informacji dostępnych przed cutoff_at"},
        {"step": 6, "name": "Feature engineering", "detail": "lagi, YoY, zwroty, zmienność, FX i cechy sektorowe"},
        {"step": 7, "name": "Dataset modelowy", "detail": "Panel spółka × kwartał oraz target t+1"},
    ]
    return {
        "pipeline": pipeline,
        "ranges": dict(ranges) if ranges else {},
        "companies": [dict(r) for r in companies],
        "quarters": [dict(r) for r in quarters],
        "concepts": [dict(r) for r in concepts],
        "macro_series": [dict(r) for r in macro],
        "checks": dict(checks) if checks else {},
        "quality": quality,
    }


@app.get("/api/v1/data-browser/catalog")
def data_browser_catalog():
    """Metadane filtrów i dostępnych zbiorów dla interaktywnego podglądu danych."""
    try:
        return get_browser_catalog()
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@app.get("/api/v1/data-browser/rows")
def data_browser_rows(
    dataset: str = Query("fundamentals", pattern="^(market|fundamentals|macro|panel)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    sort: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    ticker: str | None = Query(None),
    concept: str | None = Query(None),
    series: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None, max_length=120),
    include_history: bool = Query(False),
    has_target: bool = Query(False),
):
    """Paginowany, filtrowany i sortowany podgląd danych bez dowolnego SQL od użytkownika."""
    try:
        return browse_data(
            dataset, page=page, page_size=page_size, sort=sort, order=order, ticker=ticker,
            concept=concept, series=series, date_from=date_from, date_to=date_to, search=search,
            include_history=include_history, has_target=has_target,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@app.get("/api/v1/dashboard/ingestion-runs")
def ingestion_runs(limit: int = Query(20, ge=1, le=100)):
    with get_engine().connect() as conn:
        rows = conn.execute(text("""
            SELECT id, source_name, status, records_received, started_at, finished_at, details
            FROM metadata.ingestion_run ORDER BY started_at DESC LIMIT :limit
        """), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@app.post("/api/v1/admin/ingest")
def trigger_ingestion(start_year: int = Query(2018, ge=2000, le=date.today().year)):
    try:
        return run_full_ingestion(start_year=start_year)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@app.post("/api/v1/admin/train")
def trigger_training(
    target: str = Query("net_income", pattern="^(net_income|revenue|net_interest_income)$"),
    min_common_eval_rows: int = Query(20, ge=5, le=10000),
):
    try:
        return train_models_from_db(target=target, min_common_eval_rows=min_common_eval_rows)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
