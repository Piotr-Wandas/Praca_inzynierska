# v5 — dłuższa historia fundamentów, dynamiczne cechy i dashboard jakości

## Co zmieniono

1. **Bankier.pl jako źródło długiej historii kwartalnej** — nowy adapter `BankierFinancialClient` pobiera publiczne tabele kwartalne (RZiS, bilans, przepływy), wartości oraz wiersz `Data publikacji/aktualizacji raportu`. Dane od `--start-year` są zapisywane do `core.financial_fact`.
2. **Yahoo Finance jako fallback** — po Bankierze Yahoo uzupełnia tylko brakujące kombinacje spółka / koncept / kwartał. Nie nadpisuje dłuższej historii Bankier.
3. **Dynamiczne filtrowanie cech w walk-forward** — lag4/YoY nie są już wysyłane do `SimpleImputer`, jeśli w konkretnym foldzie są całkowicie puste. Gdy w późniejszych foldach pojawia się wystarczająca historia, cecha automatycznie wraca do modelu.
4. **Dashboard jakości datasetu** — `/dashboard` pokazuje pokrycie targetu, liczbę kwartałów, gotowość spółek na lag4, pokrycie każdej cechy, pochodzenie fundamentów oraz rekomendacje.
5. **Endpoint jakości** — `GET /api/v1/dashboard/data-quality`.
6. **Raport CLI** — `python scripts/data_quality_report.py`.

## Ważne metodologicznie

Bankier i Yahoo są źródłami agregującymi używanymi do budowy prototypu i dłuższego szeregu. Przed finalnym raportowaniem wyników badawczych wartości oraz `publication_date/available_at` powinny zostać zweryfikowane z raportami emitentów, ESPI lub ESEF. Rekordy z Yahoo, dla których brak dokładnej daty publikacji, pozostają oznaczone `availability_proxy_120d`.

## Aktualizacja działającej instalacji v4 bez kasowania bazy

```powershell
docker compose down
docker compose build --no-cache api web
docker compose up -d
```

Nie używaj `-v`, jeżeli chcesz zachować istniejące dane PostgreSQL.

## Pobranie dłuższej historii dla 5 spółek testowych

```powershell
docker compose exec api python scripts/ingest_internet_data.py --start-year 2018 --tickers PKO PEO ORL CDR DNP
```

W wyniku powinieneś zobaczyć m.in.:

```text
bankier_fundamentals.rows
bankier_fundamentals.by_company
yahoo_fundamental_fallback_rows
market_rows
nbp_rows
```

## Kontrola jakości przed treningiem

```powershell
docker compose exec api python scripts/data_quality_report.py
```

Zwróć uwagę przede wszystkim na:

- `dataset.periods`,
- `dataset.known_targets`,
- `dataset.lag4_ready_companies`,
- `features[].coverage`,
- `sources[].exact_date_rows`,
- `sources[].proxy_date_rows`.

## Trening

```powershell
docker compose exec api python scripts/train_from_database.py
```

Cechy bez danych są pomijane **osobno w każdym foldzie**, więc ostrzeżenia `Skipping features without any observed values` nie powinny już występować.

## Dashboard

- `http://localhost:3000/dashboard`
- `http://localhost:3000/models`
- `http://localhost:8000/docs`

Dashboard pokazuje teraz sekcje **Jakość datasetu**, **Kompletność cech**, **Gotowość lag4 / YoY** oraz **Źródła fundamentów**.
