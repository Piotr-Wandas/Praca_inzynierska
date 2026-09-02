-- Financial Prediction Platform - PostgreSQL schema for semester II
-- Purpose: complete, readable SQL artifact for the engineering thesis.
-- Run against an existing PostgreSQL database, e.g.:
-- psql -U fp_app -d financial_platform -f sql/create_database.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS metadata;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS app;

-- =============================
-- METADATA / DATA LINEAGE
-- =============================
CREATE TABLE IF NOT EXISTS metadata.data_source (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    source_type VARCHAR(40) NOT NULL,
    base_url TEXT,
    license_notes TEXT,
    is_official BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS metadata.ingestion_run (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data_source_id BIGINT REFERENCES metadata.data_source(id),
    source_name VARCHAR(80) NOT NULL,
    resource_url TEXT,
    request_parameters JSONB,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(30) NOT NULL DEFAULT 'started',
    records_received INTEGER,
    checksum_sha256 CHAR(64),
    parser_version VARCHAR(50),
    raw_location TEXT,
    details TEXT,
    CONSTRAINT ck_ingestion_status CHECK (status IN ('started','success','warning','failed'))
);

CREATE TABLE IF NOT EXISTS metadata.data_quality_result (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES metadata.ingestion_run(id) ON DELETE CASCADE,
    check_code VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    passed BOOLEAN NOT NULL,
    observed_value TEXT,
    expected_rule TEXT,
    details TEXT,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_quality_severity CHECK (severity IN ('info','warning','error','critical'))
);

-- =============================
-- REFERENCE / COMPANIES / INDEXES
-- =============================
CREATE TABLE IF NOT EXISTS core.sector (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    is_financial BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS core.company (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    ticker VARCHAR(32) NOT NULL,
    isin VARCHAR(16),
    lei VARCHAR(32),
    sector_id BIGINT REFERENCES core.sector(id),
    industry VARCHAR(150),
    reporting_currency CHAR(3) NOT NULL DEFAULT 'PLN',
    first_listing_date DATE,
    delisting_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_company_ticker UNIQUE (ticker),
    CONSTRAINT uq_company_isin UNIQUE (isin)
);

CREATE TABLE IF NOT EXISTS core.company_identifier (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES core.company(id) ON DELETE CASCADE,
    source_code VARCHAR(50) NOT NULL,
    identifier_type VARCHAR(50) NOT NULL,
    identifier_value VARCHAR(200) NOT NULL,
    valid_from DATE,
    valid_to DATE,
    CONSTRAINT uq_company_identifier UNIQUE (source_code, identifier_type, identifier_value)
);

CREATE TABLE IF NOT EXISTS core.market_index (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    exchange_code VARCHAR(20) NOT NULL DEFAULT 'GPW'
);

CREATE TABLE IF NOT EXISTS core.index_membership (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    market_index_id BIGINT NOT NULL REFERENCES core.market_index(id),
    company_id BIGINT NOT NULL REFERENCES core.company(id),
    valid_from DATE NOT NULL,
    valid_to DATE,
    source TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_index_membership UNIQUE (market_index_id, company_id, valid_from),
    CONSTRAINT ck_index_membership_dates CHECK (valid_to IS NULL OR valid_to >= valid_from)
);

-- =============================
-- MARKET DATA
-- =============================
CREATE TABLE IF NOT EXISTS core.daily_price (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES core.company(id),
    trade_date DATE NOT NULL,
    open NUMERIC(20,6) NOT NULL,
    high NUMERIC(20,6) NOT NULL,
    low NUMERIC(20,6) NOT NULL,
    close NUMERIC(20,6) NOT NULL,
    adjusted_close NUMERIC(20,6),
    volume NUMERIC(24,2),
    turnover NUMERIC(24,2),
    available_at TIMESTAMPTZ NOT NULL,
    ingestion_run_id BIGINT REFERENCES metadata.ingestion_run(id),
    CONSTRAINT uq_daily_price UNIQUE (company_id, trade_date),
    CONSTRAINT ck_daily_price_positive CHECK (open >= 0 AND high >= 0 AND low >= 0 AND close >= 0),
    CONSTRAINT ck_daily_price_ohlc CHECK (high >= GREATEST(open, low, close) AND low <= LEAST(open, high, close)),
    CONSTRAINT ck_daily_price_volume CHECK (volume IS NULL OR volume >= 0)
);

CREATE TABLE IF NOT EXISTS core.index_quote (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    market_index_id BIGINT NOT NULL REFERENCES core.market_index(id),
    trade_date DATE NOT NULL,
    close NUMERIC(20,6) NOT NULL,
    available_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_index_quote UNIQUE (market_index_id, trade_date)
);

-- =============================
-- FUNDAMENTAL DATA / REPORT VERSIONING
-- =============================
CREATE TABLE IF NOT EXISTS core.financial_report (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES core.company(id),
    report_type VARCHAR(30) NOT NULL,
    period_start DATE,
    period_end DATE NOT NULL,
    publication_date TIMESTAMPTZ NOT NULL,
    available_at TIMESTAMPTZ NOT NULL,
    consolidated BOOLEAN NOT NULL DEFAULT TRUE,
    source_url TEXT,
    source_report_id VARCHAR(200),
    revision_no INTEGER NOT NULL DEFAULT 1,
    supersedes_report_id BIGINT REFERENCES core.financial_report(id),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_report_type CHECK (report_type IN ('Q1','H1','Q3','FY','OTHER')),
    CONSTRAINT ck_report_publication CHECK (publication_date::date >= period_end),
    CONSTRAINT ck_report_availability CHECK (available_at >= publication_date)
);

CREATE TABLE IF NOT EXISTS core.financial_concept (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name_pl VARCHAR(200) NOT NULL,
    statement_type VARCHAR(30),
    value_type VARCHAR(30) NOT NULL DEFAULT 'flow',
    applicable_to VARCHAR(30) NOT NULL DEFAULT 'all',
    description TEXT,
    CONSTRAINT ck_concept_value_type CHECK (value_type IN ('flow','instant','ratio','per_share')),
    CONSTRAINT ck_concept_applicable CHECK (applicable_to IN ('all','financial','non_financial'))
);

CREATE TABLE IF NOT EXISTS core.concept_mapping (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT REFERENCES core.company(id),
    taxonomy VARCHAR(100),
    source_concept VARCHAR(300) NOT NULL,
    source_label VARCHAR(500),
    financial_concept_id BIGINT NOT NULL REFERENCES core.financial_concept(id),
    valid_from DATE,
    valid_to DATE,
    mapping_method VARCHAR(30) NOT NULL DEFAULT 'manual',
    confidence NUMERIC(5,4),
    manually_approved BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    CONSTRAINT ck_mapping_confidence CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE TABLE IF NOT EXISTS core.financial_fact (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES core.company(id),
    financial_report_id BIGINT REFERENCES core.financial_report(id),
    financial_concept_id BIGINT NOT NULL REFERENCES core.financial_concept(id),
    value NUMERIC(28,6) NOT NULL,
    unit VARCHAR(20) NOT NULL DEFAULT 'PLN',
    period_start DATE,
    period_end DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL DEFAULT 'quarter',
    publication_date TIMESTAMPTZ NOT NULL,
    available_at TIMESTAMPTZ NOT NULL,
    source_label VARCHAR(500),
    source_concept VARCHAR(300),
    revision_no INTEGER NOT NULL DEFAULT 1,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    ingestion_run_id BIGINT REFERENCES metadata.ingestion_run(id),
    CONSTRAINT ck_fact_period CHECK (period_type IN ('quarter','ytd','year','instant')),
    CONSTRAINT ck_fact_available CHECK (available_at >= publication_date),
    CONSTRAINT ck_fact_validity CHECK (valid_to IS NULL OR valid_to >= valid_from),
    CONSTRAINT uq_financial_fact_version UNIQUE (
        company_id, financial_concept_id, period_end, publication_date, revision_no
    )
);


-- =============================
-- STAGING / MAPPING AUDIT (v5.3 DATA FIX)
-- =============================
CREATE TABLE IF NOT EXISTS staging.financial_mapping_audit (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES metadata.ingestion_run(id) ON DELETE CASCADE,
    company_id BIGINT NOT NULL REFERENCES core.company(id),
    source_code VARCHAR(50) NOT NULL DEFAULT 'BANKIER',
    statement_name VARCHAR(80) NOT NULL,
    source_label VARCHAR(500) NOT NULL,
    normalized_label VARCHAR(500),
    mapped_concept_code VARCHAR(80),
    match_method VARCHAR(50),
    confidence NUMERIC(5,4),
    reason VARCHAR(150),
    values_observed INTEGER NOT NULL DEFAULT 0,
    first_period DATE,
    last_period DATE,
    source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_mapping_audit_confidence CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX IF NOT EXISTS ix_financial_mapping_audit_company_run
    ON staging.financial_mapping_audit(company_id, ingestion_run_id);
CREATE INDEX IF NOT EXISTS ix_financial_mapping_audit_unmatched
    ON staging.financial_mapping_audit(mapped_concept_code, values_observed DESC);

-- =============================
-- MACRO DATA
-- =============================
CREATE TABLE IF NOT EXISTS core.macro_series (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(40),
    frequency VARCHAR(20) NOT NULL,
    source_code VARCHAR(50) NOT NULL,
    description TEXT,
    CONSTRAINT ck_macro_frequency CHECK (frequency IN ('daily','monthly','quarterly','annual'))
);

CREATE TABLE IF NOT EXISTS core.macro_observation (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    macro_series_id BIGINT NOT NULL REFERENCES core.macro_series(id),
    observation_date DATE NOT NULL,
    value NUMERIC(24,8) NOT NULL,
    publication_date TIMESTAMPTZ,
    available_at TIMESTAMPTZ NOT NULL,
    ingestion_run_id BIGINT REFERENCES metadata.ingestion_run(id),
    CONSTRAINT uq_macro_observation UNIQUE (macro_series_id, observation_date, available_at)
);

-- =============================
-- ML / EXPERIMENTS / PREDICTIONS
-- =============================
CREATE TABLE IF NOT EXISTS ml.dataset_version (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_code VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    cutoff_from TIMESTAMPTZ,
    cutoff_to TIMESTAMPTZ,
    row_count INTEGER,
    feature_count INTEGER,
    git_commit VARCHAR(64),
    dvc_revision VARCHAR(128),
    checksum_sha256 CHAR(64),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS ml.experiment (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    target_code VARCHAR(80) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ml.training_run (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT REFERENCES ml.experiment(id),
    dataset_version_id BIGINT REFERENCES ml.dataset_version(id),
    model_name VARCHAR(120) NOT NULL,
    target_code VARCHAR(80) NOT NULL,
    train_from DATE,
    train_to DATE,
    validation_from DATE,
    validation_to DATE,
    hyperparameters JSONB,
    metrics JSONB,
    artifact_uri TEXT,
    git_commit VARCHAR(64),
    status VARCHAR(30) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_training_status CHECK (status IN ('started','completed','failed','rejected'))
);

CREATE TABLE IF NOT EXISTS ml.feature_importance (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    training_run_id BIGINT NOT NULL REFERENCES ml.training_run(id) ON DELETE CASCADE,
    feature_name VARCHAR(150) NOT NULL,
    importance_type VARCHAR(30) NOT NULL,
    importance_value NUMERIC(20,10) NOT NULL,
    fold_no INTEGER,
    CONSTRAINT uq_feature_importance UNIQUE (training_run_id, feature_name, importance_type, fold_no)
);

CREATE TABLE IF NOT EXISTS ml.prediction (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES core.company(id),
    training_run_id BIGINT REFERENCES ml.training_run(id),
    dataset_version_id BIGINT REFERENCES ml.dataset_version(id),
    target_code VARCHAR(80) NOT NULL,
    target_period_end DATE NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    cutoff_at TIMESTAMPTZ NOT NULL,
    predicted_value NUMERIC(28,6) NOT NULL,
    lower_bound NUMERIC(28,6),
    upper_bound NUMERIC(28,6),
    actual_value NUMERIC(28,6),
    actual_available_at TIMESTAMPTZ,
    absolute_error NUMERIC(28,6),
    CONSTRAINT uq_prediction UNIQUE (company_id, training_run_id, target_code, target_period_end, cutoff_at)
);

-- =============================
-- INDEXES FOR EXPECTED QUERY PATTERNS
-- =============================
CREATE INDEX IF NOT EXISTS ix_ingestion_run_status_started
    ON metadata.ingestion_run (status, started_at DESC);
CREATE INDEX IF NOT EXISTS ix_index_membership_company_dates
    ON core.index_membership (company_id, valid_from, valid_to);
CREATE INDEX IF NOT EXISTS ix_daily_price_company_date
    ON core.daily_price (company_id, trade_date DESC);
CREATE INDEX IF NOT EXISTS ix_daily_price_available
    ON core.daily_price (company_id, available_at DESC);
CREATE INDEX IF NOT EXISTS ix_financial_fact_company_period
    ON core.financial_fact (company_id, period_end DESC);
CREATE INDEX IF NOT EXISTS ix_financial_fact_concept_period
    ON core.financial_fact (financial_concept_id, period_end DESC);
CREATE INDEX IF NOT EXISTS ix_financial_fact_point_in_time
    ON core.financial_fact (company_id, financial_concept_id, available_at DESC);
CREATE INDEX IF NOT EXISTS ix_macro_obs_series_available
    ON core.macro_observation (macro_series_id, available_at DESC);
CREATE INDEX IF NOT EXISTS ix_prediction_company_period
    ON ml.prediction (company_id, target_period_end DESC);
CREATE INDEX IF NOT EXISTS ix_training_run_model_created
    ON ml.training_run (model_name, created_at DESC);

-- =============================
-- REFERENCE VALUES
-- =============================
INSERT INTO core.market_index(code, name, exchange_code)
VALUES ('WIG20', 'WIG20', 'GPW')
ON CONFLICT (code) DO NOTHING;

INSERT INTO core.financial_concept(code, name_pl, statement_type, value_type, applicable_to, description)
VALUES
 ('NET_INCOME_PARENT', 'Zysk netto przypisany akcjonariuszom jednostki dominującej', 'income_statement', 'flow', 'all', 'Preferowany target, gdy źródło raportuje udział jednostki dominującej.'),
 ('NET_INCOME', 'Zysk netto', 'income_statement', 'flow', 'all', 'Fallback target, gdy źródło nie rozróżnia wyniku przypisanego jednostce dominującej.'),
 ('EPS_BASIC', 'Podstawowy zysk na akcję', 'income_statement', 'per_share', 'all', 'Target pomocniczy po kontroli zmian liczby akcji.'),
 ('REVENUE', 'Przychody ze sprzedaży', 'income_statement', 'flow', 'non_financial', 'Target dla spółek niefinansowych.'),
 ('OPERATING_PROFIT', 'Wynik operacyjny', 'income_statement', 'flow', 'non_financial', NULL),
 ('EBITDA', 'EBITDA', 'income_statement', 'flow', 'non_financial', 'Używać tylko, gdy raportowanie jest spójne.'),
 ('NET_INTEREST_INCOME', 'Wynik odsetkowy', 'income_statement', 'flow', 'financial', 'Target sektorowy dla banków.'),
 ('NET_FEE_INCOME', 'Wynik z tytułu opłat i prowizji', 'income_statement', 'flow', 'financial', 'Cecha/target sektorowy dla banków.'),
 ('TOTAL_ASSETS', 'Aktywa razem', 'balance_sheet', 'instant', 'all', NULL),
 ('EQUITY', 'Kapitał własny', 'balance_sheet', 'instant', 'all', NULL),
 ('OPERATING_CASH_FLOW', 'Przepływy pieniężne z działalności operacyjnej', 'cash_flow', 'flow', 'non_financial', NULL)
ON CONFLICT (code) DO NOTHING;

COMMIT;
