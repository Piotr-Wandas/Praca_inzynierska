-- Analytical views used by feature engineering and presentation layer.

CREATE OR REPLACE VIEW analytics.v_current_wig20_members AS
SELECT c.id AS company_id, c.ticker, c.name, s.name AS sector
FROM core.index_membership im
JOIN core.market_index mi ON mi.id = im.market_index_id
JOIN core.company c ON c.id = im.company_id
LEFT JOIN core.sector s ON s.id = c.sector_id
WHERE mi.code = 'WIG20'
  AND im.valid_from <= CURRENT_DATE
  AND (im.valid_to IS NULL OR im.valid_to >= CURRENT_DATE);

CREATE OR REPLACE VIEW analytics.v_financial_facts_current AS
SELECT ff.*, fc.code AS concept_code, fc.name_pl AS concept_name
FROM core.financial_fact ff
JOIN core.financial_concept fc ON fc.id = ff.financial_concept_id
WHERE ff.is_current = TRUE;

CREATE OR REPLACE VIEW analytics.v_model_comparison AS
SELECT
    tr.model_name,
    tr.target_code,
    COUNT(*) AS runs,
    AVG(NULLIF(tr.metrics ->> 'mae', '')::numeric) AS avg_mae,
    AVG(NULLIF(tr.metrics ->> 'rmse', '')::numeric) AS avg_rmse,
    AVG(NULLIF(tr.metrics ->> 'smape', '')::numeric) AS avg_smape
FROM ml.training_run tr
WHERE tr.status = 'completed'
GROUP BY tr.model_name, tr.target_code;

CREATE OR REPLACE VIEW analytics.v_predictions_vs_actuals AS
SELECT
    p.company_id,
    c.ticker,
    p.target_code,
    p.target_period_end,
    p.cutoff_at,
    p.predicted_value,
    p.actual_value,
    CASE WHEN p.actual_value IS NOT NULL THEN abs(p.predicted_value - p.actual_value) END AS absolute_error,
    tr.model_name
FROM ml.prediction p
JOIN core.company c ON c.id = p.company_id
LEFT JOIN ml.training_run tr ON tr.id = p.training_run_id;
