-- Kontrole odczytowe dla schematu z 01_create_database.sql.
-- Uruchomić po załadowaniu danych. Wynik nie stanowi certyfikatu point-in-time.
BEGIN TRANSACTION READ ONLY;
SELECT 'company' AS obiekt, count(*) AS liczba FROM core.company
UNION ALL SELECT 'financial_fact', count(*) FROM core.financial_fact
UNION ALL SELECT 'daily_price', count(*) FROM core.daily_price
UNION ALL SELECT 'prediction', count(*) FROM ml.prediction;

-- Więcej niż jeden fakt bieżący tego samego pojęcia i okresu.
SELECT company_id, financial_concept_id, period_end, period_type, count(*)
FROM core.financial_fact WHERE is_current
GROUP BY company_id, financial_concept_id, period_end, period_type HAVING count(*) > 1;

-- Przybliżone daty dostępności wymagają sprawdzenia w źródłach.
SELECT count(*) AS wszystkie,
       count(*) FILTER (WHERE source_label ILIKE '%availability_proxy%') AS proxy
FROM core.financial_fact WHERE is_current;

-- Luki w kolejnych okresach kwartalnych.
WITH okresy AS (
  SELECT DISTINCT company_id, period_end FROM core.financial_fact
  WHERE is_current AND period_type = 'quarter'
), kolejne AS (
  SELECT *, lead(period_end) OVER (PARTITION BY company_id ORDER BY period_end) AS nastepny
  FROM okresy
)
SELECT * FROM kolejne WHERE nastepny IS NOT NULL
AND (extract(year FROM nastepny)*4 + extract(quarter FROM nastepny))
  - (extract(year FROM period_end)*4 + extract(quarter FROM period_end)) <> 1;

-- Estymacja po zakończeniu kwartału nie jest prognozą przed jego końcem.
SELECT target_code, count(*) AS predykcje,
       count(*) FILTER (WHERE cutoff_at::date > target_period_end) AS po_koncu_kwartalu
FROM ml.prediction GROUP BY target_code;
COMMIT;
