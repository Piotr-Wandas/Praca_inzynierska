-- Read-only diagnostics that can be shown during semester-II assessment.

-- 1. Duplicate market observations (expected: zero rows)
SELECT company_id, trade_date, COUNT(*) AS duplicates
FROM core.daily_price
GROUP BY company_id, trade_date
HAVING COUNT(*) > 1;

-- 2. Invalid OHLC records (expected: zero rows)
SELECT *
FROM core.daily_price
WHERE high < GREATEST(open, low, close)
   OR low > LEAST(open, high, close)
   OR volume < 0;

-- 3. Financial information published before the reporting period ended (expected: zero rows)
SELECT id, company_id, period_end, publication_date
FROM core.financial_fact
WHERE publication_date::date < period_end;

-- 4. Potential point-in-time violation in stored predictions (expected: zero rows)
SELECT p.id, p.company_id, p.cutoff_at, ff.available_at
FROM ml.prediction p
JOIN core.financial_fact ff
  ON ff.company_id = p.company_id
WHERE ff.available_at > p.cutoff_at
  AND ff.period_end < p.target_period_end;
