# Financial Prediction Platform — v5.3 DATA FIX

Prototyp pracy inżynierskiej: pobieranie rzeczywistych danych, PostgreSQL, point-in-time feature engineering, audyt mapowania pozycji finansowych, walk-forward ML i dashboard Next.js.

Najważniejsza instrukcja uruchomienia: **`V5_3_DATA_FIX.md`**.

Aktualna wersja rozszerza prototyp o kanoniczny target zysku netto, wspólną próbkę ewaluacyjną i diagnostykę dashboardu. Szczegóły: `V5_2_COMPLETE.md`.

# WIG20 Financial Prediction Platform — prototyp na II semestr

Wstępna implementacja do pracy inżynierskiej **„Model predykcji wyników finansowych spółek giełdowych”**.

## Co już pokazuje prototyp

- modularną strukturę repozytorium,
- PostgreSQL + Alembic i schematy `metadata/raw/staging/core/analytics/ml/app`,
- model tabel dla spółek, składu indeksu, notowań, faktów finansowych, makro, treningów i predykcji,
- adapter NBP Web API,
- pomocniczy adapter Stooq dla danych rynkowych,
- prototyp importu danych fundamentalnych z ustrukturyzowanego CSV,
- walidację OHLCV,
- test przeciwko look-ahead bias (`available_at <= cutoff_at`),
- dwa baseline'y,
- model Ridge i HistGradientBoostingRegressor,
- walidację walk-forward,
- przepływ Prefect,
- endpointy FastAPI,
- pierwszy ekran Next.js,
- CI GitHub Actions.

## Ważne

Plik `data/demo/panel_demo.csv` zawiera **syntetyczne dane testowe** służące wyłącznie do sprawdzenia działania pipeline'u. Wyników z tego pliku nie wolno przedstawiać jako wyników pracy badawczej.

## Uruchomienie testów na Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
python -m financial_platform.modeling.demo_pipeline
```

## Uruchomienie usług Docker

```powershell
Copy-Item .env.example .env
docker compose up -d --build
alembic upgrade head
```

Po uruchomieniu:
- API: http://localhost:8000/docs
- Frontend: http://localhost:3000
- MLflow: http://localhost:5000
- Prefect: http://localhost:4200

## Co trzeba zrobić przed zaliczeniem

1. Podłączyć prawdziwy katalog spółek i historię WIG20 z GPW Benchmark.
2. Wykonać realne pobranie notowań i makro dla co najmniej 4–6 spółek.
3. Zaimportować rzeczywiste dane fundamentalne z datami publikacji dla pilotażu.
4. Zbudować rzeczywisty point-in-time dataset i uruchomić te same testy leakage.
5. Zapisać co najmniej jeden realny eksperyment w MLflow.
6. Wstawić screenshot działającego przepływu i aplikacji do materiałów na zaliczenie.

## Ekrany interfejsu II semestru

Po uruchomieniu `docker compose up -d --build` dostępne są:

- `http://localhost:3000/` – strona główna,
- `http://localhost:3000/companies` – lista spółek,
- `http://localhost:3000/companies/PKO` – przykładowa strona szczegółów spółki,
- `http://localhost:3000/models` – porównanie modeli.

Wartości prognoz i metryk widoczne w UI są oznaczone jako demonstracyjne. Finalnie mają być zastąpione danymi z PostgreSQL/MLflow. Lista spółek w UI również jest warstwą demonstracyjną; historia rzeczywistego członkostwa w WIG20 ma pochodzić z `core.index_membership`.

## Semester-II database and analysis artifacts

For the assessment-ready SQL schema and reproducible analytical code, see:

- `sql/create_database.sql` — full PostgreSQL DDL,
- `sql/views/analytics_views.sql` — analytical views,
- `sql/diagnostics/quality_checks.sql` — data-quality diagnostics,
- `scripts/run_analysis.py` — reproducible model-comparison script,
- `docs/database/SEMESTER2_DATABASE_AND_ANALYSIS.md` — exact run instructions.

Run the demo analysis:

```powershell
python .\scripts\run_analysis.py
```

The current `data/demo` values are synthetic and exist only to demonstrate the pipeline. They are not thesis research results.

## v4: internet data + PostgreSQL + analytical dashboard

See `REAL_DATA_DASHBOARD.md`. Main commands:

```bash
docker compose up -d --build
docker compose exec api python scripts/init_database.py
docker compose exec api python scripts/full_refresh.py --start-year 2018
```

Dashboard: `http://localhost:3000/dashboard`.

## v5 — long-history fundamentals and data-quality dashboard

Aktualizacja v5 dodaje dłuższą historię kwartalną z publicznych tabel Bankier.pl, Yahoo jako fallback, dynamiczne odrzucanie pustych cech w poszczególnych foldach oraz endpoint/dashboard jakości datasetu. Instrukcja: `V5_LONG_HISTORY_QUALITY.md`.

## v5.3.1 FIX
Naprawiono PostgreSQL `AmbiguousParameter` przy zapisie `core.concept_mapping`.

## v5.4 – Dane i przygotowanie datasetu
Nowa zakładka `http://localhost:3000/data` prezentuje profesjonalny dashboard jakości i przygotowania danych: ETL, pokrycie kwartalne, kompletność cech, pokrycie konceptów, serie makro i kontrole jakości. Szczegóły: `V5_4_DATA_PREPARATION_DASHBOARD.md`.

## v5.5 — sector-aware feature coverage

Wersja v5.5 rozróżnia rzeczywiste braki danych od braków strukturalnych. Cechy bankowe są oceniane względem obserwacji sektora finansowego, a cechy przychodowe/operacyjne względem spółek niefinansowych. Globalny model zysku netto nie imputuje cech sektorowych do spółek, dla których te cechy nie mają znaczenia.

## v6.0 REVIEW RELEASE

Do oddania pracy użyj procesu opisnego w `README_START_HERE.md`. Autor tworzy snapshot przez `PREPARE_REVIEW_SNAPSHOT.bat`, następnie finalną paczkę przez `BUILD_FINAL_REVIEW_ZIP.bat`. Prowadzący uruchamia wyłącznie `START_REVIEW.bat`.
