from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Iterable

import pandas as pd
from sqlalchemy import text

from financial_platform.config.settings import get_settings
from financial_platform.config.universe import PILOT_COMPANIES
from financial_platform.db.session import get_engine
from financial_platform.ingestion.bankier_financials import BankierFinancialClient
from financial_platform.ingestion.nbp import NBPClient
from financial_platform.ingestion.yahoo_finance import YahooFinanceClient


def _source_id(conn, code: str, name: str, source_type: str, base_url: str, is_official: bool, license_notes: str) -> int:
    return conn.execute(text("""
        INSERT INTO metadata.data_source(code, name, source_type, base_url, is_official, license_notes)
        VALUES (:code, :name, :source_type, :base_url, :is_official, :license_notes)
        ON CONFLICT (code) DO UPDATE SET
            name=EXCLUDED.name, source_type=EXCLUDED.source_type, base_url=EXCLUDED.base_url,
            is_official=EXCLUDED.is_official, license_notes=EXCLUDED.license_notes
        RETURNING id
    """), dict(code=code, name=name, source_type=source_type, base_url=base_url,
                 is_official=is_official, license_notes=license_notes)).scalar_one()


def _start_run(conn, source_id: int, source_name: str, details: str) -> int:
    return conn.execute(text("""
        INSERT INTO metadata.ingestion_run(data_source_id, source_name, status, details)
        VALUES (:source_id, :source_name, 'started', :details)
        RETURNING id
    """), dict(source_id=source_id, source_name=source_name, details=details)).scalar_one()


def _finish_run(conn, run_id: int, status: str, records: int, details: str | None = None) -> None:
    conn.execute(text("""
        UPDATE metadata.ingestion_run
        SET status=:status, finished_at=now(), records_received=:records,
            details=COALESCE(:details, details)
        WHERE id=:run_id
    """), dict(status=status, records=records, details=details, run_id=run_id))


def _selected_companies(tickers: Iterable[str] | None) -> list[dict]:
    if tickers is None:
        return list(PILOT_COMPANIES)
    wanted = {str(x).upper() for x in tickers}
    return [x for x in PILOT_COMPANIES if x["ticker"].upper() in wanted]


def seed_reference_data(conn) -> dict[str, int]:
    # v5.2: ingestion sam zapewnia istnienie nowych konceptów, dzięki czemu
    # aktualizacja z v5.1 nie wymaga kasowania bazy.
    conn.execute(text("""
        INSERT INTO core.financial_concept(code, name_pl, statement_type, value_type, applicable_to, description)
        VALUES
          ('NET_INCOME', 'Zysk netto', 'income_statement', 'flow', 'all',
           'Fallback dla NET_INCOME_PARENT, gdy źródło nie rozróżnia udziału jednostki dominującej.'),
          ('NET_FEE_INCOME', 'Wynik z tytułu opłat i prowizji', 'income_statement', 'flow', 'financial',
           'Cecha sektorowa dla banków.')
        ON CONFLICT (code) DO NOTHING
    """))
    company_ids: dict[str, int] = {}
    for item in PILOT_COMPANIES:
        sector_id = conn.execute(text("""
            INSERT INTO core.sector(code, name, is_financial)
            VALUES (:code, :name, :is_financial)
            ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, is_financial=EXCLUDED.is_financial
            RETURNING id
        """), dict(code=item["sector"].upper().replace(" ", "_"), name=item["sector"],
                     is_financial=item["is_financial"])).scalar_one()
        company_id = conn.execute(text("""
            INSERT INTO core.company(name, ticker, sector_id)
            VALUES (:name, :ticker, :sector_id)
            ON CONFLICT (ticker) DO UPDATE SET name=EXCLUDED.name, sector_id=EXCLUDED.sector_id
            RETURNING id
        """), dict(name=item["name"], ticker=item["ticker"], sector_id=sector_id)).scalar_one()
        company_ids[item["ticker"]] = company_id
        for source_code, identifier in (("YAHOO", item["yahoo"]), ("BANKIER", item.get("bankier"))):
            if not identifier:
                continue
            conn.execute(text("""
                INSERT INTO core.company_identifier(company_id, source_code, identifier_type, identifier_value)
                VALUES (:company_id, :source_code, 'ticker', :identifier)
                ON CONFLICT (source_code, identifier_type, identifier_value)
                DO UPDATE SET company_id=EXCLUDED.company_id
            """), dict(company_id=company_id, source_code=source_code, identifier=identifier))
    return company_ids


def _store_financial_fact(conn, *, company_id: int, concept_id: int, row: dict, run_id: int,
                          replace_current: bool, skip_if_current: bool = False) -> bool:
    if skip_if_current:
        exists = conn.execute(text("""
            SELECT 1 FROM core.financial_fact
            WHERE company_id=:company_id AND financial_concept_id=:concept_id
              AND period_end=:period_end AND is_current=TRUE
            LIMIT 1
        """), {"company_id": company_id, "concept_id": concept_id, "period_end": row["period_end"]}).first()
        if exists:
            return False

    if replace_current:
        conn.execute(text("""
            UPDATE core.financial_fact
            SET is_current=FALSE, valid_to=now()
            WHERE company_id=:company_id AND financial_concept_id=:concept_id
              AND period_end=:period_end AND is_current=TRUE
              AND publication_date <> :publication_date
        """), {
            "company_id": company_id, "concept_id": concept_id,
            "period_end": row["period_end"], "publication_date": row["publication_date"],
        })

    conn.execute(text("""
        INSERT INTO core.financial_fact(
            company_id, financial_concept_id, value, unit, period_start, period_end,
            period_type, publication_date, available_at, source_label, source_concept, revision_no,
            ingestion_run_id, is_current, valid_from, valid_to
        ) VALUES (
            :company_id, :concept_id, :value, :unit, :period_start, :period_end,
            'quarter', :publication_date, :available_at, :source_label, :source_concept, 1,
            :run_id, TRUE, now(), NULL
        )
        ON CONFLICT (company_id, financial_concept_id, period_end, publication_date, revision_no)
        DO UPDATE SET value=EXCLUDED.value, unit=EXCLUDED.unit, available_at=EXCLUDED.available_at,
                      source_label=EXCLUDED.source_label, source_concept=EXCLUDED.source_concept, ingestion_run_id=EXCLUDED.ingestion_run_id,
                      is_current=TRUE, valid_to=NULL
    """), {
        "company_id": company_id, "concept_id": concept_id,
        "value": row["value"], "unit": row["unit"], "period_start": row.get("period_start"),
        "period_end": row["period_end"], "publication_date": row["publication_date"],
        "available_at": row["available_at"], "source_label": str(row["source_label"])[:500],
        "source_concept": str(row.get("source_concept") or "")[:300] or None,
        "run_id": run_id,
    })
    return True


def ingest_yahoo_market(start: date, end: date, tickers: Iterable[str] | None = None) -> int:
    client = YahooFinanceClient()
    total = 0
    selected = _selected_companies(tickers)
    with get_engine().begin() as conn:
        company_ids = seed_reference_data(conn)
        source_id = _source_id(conn, "YAHOO", "Yahoo Finance", "market+fundamental",
                               "https://finance.yahoo.com/", False,
                               "Prototype market source. Verify redistribution terms before public deployment.")
        run_id = _start_run(conn, source_id, "Yahoo Finance market", f"{start}..{end}")
        try:
            for item in selected:
                df = client.history(item["yahoo"], start.isoformat(), (end + timedelta(days=1)).isoformat())
                if df.empty:
                    continue
                for row in df.to_dict("records"):
                    trade_date = pd.Timestamp(row["trade_date"]).date()
                    available_at = datetime.combine(trade_date, datetime.max.time(), tzinfo=timezone.utc)
                    conn.execute(text("""
                        INSERT INTO core.daily_price(
                            company_id, trade_date, open, high, low, close, adjusted_close, volume,
                            available_at, ingestion_run_id
                        ) VALUES (
                            :company_id, :trade_date, :open, :high, :low, :close, :adjusted_close,
                            :volume, :available_at, :run_id
                        )
                        ON CONFLICT (company_id, trade_date) DO UPDATE SET
                            open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
                            close=EXCLUDED.close, adjusted_close=EXCLUDED.adjusted_close,
                            volume=EXCLUDED.volume, available_at=EXCLUDED.available_at,
                            ingestion_run_id=EXCLUDED.ingestion_run_id
                    """), {
                        "company_id": company_ids[item["ticker"]], "trade_date": trade_date,
                        "open": row.get("open"), "high": row.get("high"), "low": row.get("low"),
                        "close": row.get("close"), "adjusted_close": row.get("adjusted_close"),
                        "volume": None if pd.isna(row.get("volume")) else row.get("volume"),
                        "available_at": available_at, "run_id": run_id,
                    })
                    total += 1
            _finish_run(conn, run_id, "success", total)
        except Exception as exc:
            _finish_run(conn, run_id, "failed", total, str(exc))
            raise
    return total


def _store_mapping_audit(conn, *, company_id: int, run_id: int, audit_df: pd.DataFrame) -> int:
    if audit_df.empty:
        return 0
    inserted = 0
    for row in audit_df.to_dict("records"):
        conn.execute(text("""
            INSERT INTO staging.financial_mapping_audit(
                ingestion_run_id, company_id, source_code, statement_name,
                source_label, normalized_label, mapped_concept_code, match_method,
                confidence, reason, values_observed, first_period, last_period, source_url
            ) VALUES (
                :run_id, :company_id, 'BANKIER', :statement, :source_label,
                :normalized_label, :mapped_concept, :match_method, :confidence,
                :reason, :values_observed, :first_period, :last_period, :source_url
            )
        """), {
            "run_id": run_id,
            "company_id": company_id,
            "statement": row.get("statement"),
            "source_label": str(row.get("source_label") or "")[:500],
            "normalized_label": str(row.get("normalized_label") or "")[:500] or None,
            "mapped_concept": row.get("mapped_concept"),
            "match_method": row.get("match_method"),
            "confidence": row.get("confidence"),
            "reason": str(row.get("reason") or "")[:150] or None,
            "values_observed": int(row.get("values_observed") or 0),
            "first_period": row.get("first_period"),
            "last_period": row.get("last_period"),
            "source_url": row.get("source_url"),
        })
        inserted += 1
    return inserted


def ingest_bankier_fundamentals(start_year: int = 2018, tickers: Iterable[str] | None = None) -> dict:
    """Primary long-history fundamental loader with v5.3 mapping audit.

    v5.3 nie zgaduje po cichu nazw pozycji. Każdy wiersz źródłowy trafia do
    staging.financial_mapping_audit wraz z decyzją mapowania, pewnością i liczbą
    dostępnych obserwacji. Dzięki temu brak targetu można zdiagnozować po nazwach
    faktycznie występujących w źródle.
    """
    client = BankierFinancialClient()
    total = 0
    audit_total = 0
    by_company: dict[str, int] = {}
    audit_by_company: dict[str, int] = {}
    errors: dict[str, str] = {}
    selected = _selected_companies(tickers)
    with get_engine().begin() as conn:
        company_ids = seed_reference_data(conn)
        concept_ids = dict(conn.execute(text("SELECT code, id FROM core.financial_concept")).all())
        source_id = _source_id(
            conn, "BANKIER", "Bankier.pl / Notoria financial tables", "fundamental",
            "https://www.bankier.pl/gielda/notowania/akcje/", False,
            "Public aggregation tables for prototype ETL. Final thesis values and filing dates require issuer/ESPI/ESEF verification.",
        )
        run_id = _start_run(conn, source_id, "Bankier fundamentals v5.3", f"quarterly; start_year={start_year}; mapping audit enabled")
        try:
            for item in selected:
                slug = item.get("bankier")
                if not slug:
                    continue
                company_id = company_ids[item["ticker"]]

                # Dezaktywujemy poprzednie bieżące rekordy Bankier dla pobieranego zakresu,
                # ale zachowujemy je jako historię wersji.
                conn.execute(text("""
                    UPDATE core.financial_fact
                    SET is_current=FALSE, valid_to=now()
                    WHERE company_id=:company_id AND is_current=TRUE
                      AND period_end >= :period_from
                      AND source_label LIKE 'Bankier/%'
                """), {"company_id": company_id, "period_from": date(start_year, 1, 1)})

                try:
                    df, audit_df = client.quarterly_facts_with_audit(slug, start_year=start_year)
                except Exception as exc:
                    errors[item["ticker"]] = str(exc)
                    continue

                audit_count = _store_mapping_audit(conn, company_id=company_id, run_id=run_id, audit_df=audit_df)
                audit_total += audit_count
                audit_by_company[item["ticker"]] = audit_count

                inserted = 0
                for row in df.to_dict("records"):
                    concept_id = concept_ids.get(row["concept_code"])
                    if concept_id is None:
                        continue
                    if _store_financial_fact(
                        conn, company_id=company_id, concept_id=concept_id,
                        row=row, run_id=run_id, replace_current=True,
                    ):
                        inserted += 1
                        total += 1
                        # Utrwalamy jawne mapowanie źródłowej etykiety do konceptu.
                        # v5.3.1: jawne typy + osobny SELECT/INSERT eliminują
                        # psycopg.errors.AmbiguousParameter w PostgreSQL.
                        mapping_params = {
                            "company_id": int(company_id),
                            "source_concept": str(row.get("source_concept") or "")[:300],
                            "source_label": str(row.get("source_label") or "")[:500] or None,
                            "concept_id": int(concept_id),
                            "mapping_method": str(row.get("mapping_method") or "semantic_rule")[:30],
                            "confidence": float(row.get("mapping_confidence") or 0.0),
                        }
                        # SAVEPOINT chroni główny run przed stanem InFailedSqlTransaction
                        # w razie lokalnego problemu przy pomocniczym zapisie mapowania.
                        with conn.begin_nested():
                            already_exists = conn.execute(text("""
                                SELECT 1
                                FROM core.concept_mapping
                                WHERE company_id = :company_id
                                  AND taxonomy = 'BANKIER_NOTORIA'
                                  AND source_concept = CAST(:source_concept AS VARCHAR(300))
                                  AND financial_concept_id = :concept_id
                                LIMIT 1
                            """), mapping_params).scalar()
                            if not already_exists:
                                conn.execute(text("""
                                    INSERT INTO core.concept_mapping(
                                        company_id, taxonomy, source_concept, source_label,
                                        financial_concept_id, mapping_method, confidence,
                                        manually_approved, notes
                                    ) VALUES (
                                        :company_id, 'BANKIER_NOTORIA',
                                        CAST(:source_concept AS VARCHAR(300)),
                                        CAST(:source_label AS VARCHAR(500)),
                                        :concept_id, CAST(:mapping_method AS VARCHAR(30)),
                                        CAST(:confidence AS NUMERIC(5,4)), FALSE,
                                        'Automatyczne mapowanie v5.3.1; wymaga weryfikacji przed finalnym raportowaniem.'
                                    )
                                """), mapping_params)
                by_company[item["ticker"]] = inserted

            status = "success" if total and not errors else "warning"
            details = (
                f"v5.3 quarterly mapping; rows_by_company={by_company}; audit_rows={audit_total}; "
                f"audit_by_company={audit_by_company}; errors={errors or '{}'}; "
                "verify final thesis values with issuer/ESPI/ESEF."
            )
            _finish_run(conn, run_id, status, total, details)
        except Exception as exc:
            _finish_run(conn, run_id, "failed", total, str(exc))
            raise
    return {
        "rows": total,
        "by_company": by_company,
        "audit_rows": audit_total,
        "audit_by_company": audit_by_company,
        "errors": errors,
    }

def ingest_yahoo_fundamentals(tickers: Iterable[str] | None = None, only_missing: bool = True) -> int:
    """Fallback for concepts/periods missing after the long-history loader."""
    client = YahooFinanceClient()
    total = 0
    selected = _selected_companies(tickers)
    with get_engine().begin() as conn:
        company_ids = seed_reference_data(conn)
        concept_ids = dict(conn.execute(text("SELECT code, id FROM core.financial_concept")).all())
        source_id = _source_id(conn, "YAHOO", "Yahoo Finance", "market+fundamental",
                               "https://finance.yahoo.com/", False,
                               "Fallback fundamental source. Filing availability may use a conservative +120d proxy.")
        run_id = _start_run(conn, source_id, "Yahoo Finance fundamentals fallback", "quarterly statements; only missing facts")
        try:
            for item in selected:
                df = client.quarterly_facts(item["yahoo"])
                if df.empty:
                    continue
                for row in df.to_dict("records"):
                    concept_id = concept_ids.get(row["concept_code"])
                    if concept_id is None:
                        continue
                    inserted = _store_financial_fact(
                        conn, company_id=company_ids[item["ticker"]], concept_id=concept_id,
                        row=row, run_id=run_id, replace_current=False, skip_if_current=only_missing,
                    )
                    total += int(inserted)
            _finish_run(conn, run_id, "warning" if total == 0 else "success", total,
                        "Fallback only. Yahoo publication timestamps may use marked +120d proxies.")
        except Exception as exc:
            _finish_run(conn, run_id, "failed", total, str(exc))
            raise
    return total


def ingest_nbp_fx(start: date, end: date, currencies: tuple[str, ...] = ("EUR", "USD", "CHF")) -> int:
    client = NBPClient()
    total = 0
    with get_engine().begin() as conn:
        source_id = _source_id(conn, "NBP", "Narodowy Bank Polski Web API", "macro",
                               "https://api.nbp.pl/", True, "Official public NBP Web API.")
        run_id = _start_run(conn, source_id, "NBP FX", f"{start}..{end}; {currencies}")
        try:
            for currency in currencies:
                df = client.fetch_fx(currency, start, end)
                if df.empty:
                    continue
                for row in df.to_dict("records"):
                    series_id = conn.execute(text("""
                        INSERT INTO core.macro_series(code, name, unit, frequency, source_code)
                        VALUES (:series_code, :name, :unit, :frequency, :source_code)
                        ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name
                        RETURNING id
                    """), row).scalar_one()
                    conn.execute(text("""
                        INSERT INTO core.macro_observation(
                            macro_series_id, observation_date, value, publication_date, available_at,
                            ingestion_run_id
                        ) VALUES (:series_id, :observation_date, :value, :publication_date,
                                  :available_at, :run_id)
                        ON CONFLICT (macro_series_id, observation_date, available_at)
                        DO UPDATE SET value=EXCLUDED.value, ingestion_run_id=EXCLUDED.ingestion_run_id
                    """), {**row, "series_id": series_id, "run_id": run_id})
                    total += 1
            _finish_run(conn, run_id, "success", total)
        except Exception as exc:
            _finish_run(conn, run_id, "failed", total, str(exc))
            raise
    return total


def run_full_ingestion(start_year: int | None = None, tickers: list[str] | None = None) -> dict:
    settings = get_settings()
    year = start_year or settings.data_start_year
    start = date(year, 1, 1)
    end = date.today()
    result = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "range": [start.isoformat(), end.isoformat()],
        "tickers": tickers or [x["ticker"] for x in PILOT_COMPANIES],
    }
    result["market_rows"] = ingest_yahoo_market(start, end, tickers=tickers)
    result["bankier_fundamentals"] = ingest_bankier_fundamentals(start_year=year, tickers=tickers)
    result["yahoo_fundamental_fallback_rows"] = ingest_yahoo_fundamentals(tickers=tickers, only_missing=True)
    result["fundamental_rows"] = (
        int(result["bankier_fundamentals"]["rows"]) + int(result["yahoo_fundamental_fallback_rows"])
    )
    result["nbp_rows"] = ingest_nbp_fx(start, end)
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    return result
