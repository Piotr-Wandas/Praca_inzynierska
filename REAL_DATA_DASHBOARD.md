# Real-data pipeline + dashboard

Ta wersja rozszerza prototyp o rzeczywisty przepływ danych:

`Internet -> PostgreSQL -> point-in-time feature set -> walk-forward ML -> ml.* -> FastAPI -> Next.js dashboard`

## Źródła

1. **Yahoo Finance / yfinance** – prototypowe notowania i kwartalne sprawozdania finansowe dla spółek GPW. Dane są zapisywane ze źródłem i identyfikatorem Yahoo. Jeżeli dokładna data publikacji raportu nie jest dostępna, loader zapisuje konserwatywny proxy `period_end + 120 dni` i oznacza rekord w `source_label`. Takich dat nie wolno traktować jako finalnych dat raportowych w pracy; przed końcowym eksperymentem trzeba je zweryfikować w ESPI/ESEF/raportach emitenta.
2. **NBP Web API** – EUR/PLN, USD/PLN i CHF/PLN. Adapter automatycznie dzieli zakres na porcje do 93 dni.
3. **GUS BDL API** – dodany jest adapter konfigurowalny identyfikatorem zmiennej. Konkretne zmienne powinny być wybrane i udokumentowane w pracy przed ich włączeniem do datasetu.
4. **Stooq** – dotychczasowy adapter pozostaje w projekcie. W 2026 automatyczny CSV wymaga klucza API; klucz można przekazać przez `STOOQ_API_KEY`. Główny automatyczny przebieg v4 używa Yahoo jako źródła rynkowego, żeby pipeline działał bez klucza Stooq.

## Pierwsze uruchomienie na czystej bazie

```powershell
docker compose down -v
docker compose up -d --build
```

PostgreSQL wykona `sql/create_database.sql` automatycznie przy utworzeniu nowego wolumenu.

Jeżeli chcesz zachować istniejący wolumen:

```powershell
docker compose up -d --build
docker compose exec api python scripts/init_database.py
```

## Pobranie danych z internetu

Pełne uniwersum pilotażowe:

```powershell
docker compose exec api python scripts/ingest_internet_data.py --start-year 2018
```

Szybszy test na kilku spółkach:

```powershell
docker compose exec api python scripts/ingest_internet_data.py --start-year 2020 --tickers PKO PEO ORL CDR DNP
```

## Trening modeli z PostgreSQL

```powershell
docker compose exec api python scripts/train_from_database.py
```

Całość jednym poleceniem:

```powershell
docker compose exec api python scripts/full_refresh.py --start-year 2018
```

## Aplikacja

- Start: http://localhost:3000
- Dashboard: http://localhost:3000/dashboard
- Spółki: http://localhost:3000/companies
- Modele: http://localhost:3000/models
- FastAPI docs: http://localhost:8000/docs
- MLflow: http://localhost:5000
- Prefect: http://localhost:4200

## Co pokazuje dashboard

- liczbę spółek i rekordów rynkowych/fundamentalnych/makro,
- pokrycie danych dla każdej spółki,
- historię pobrań ETL z `metadata.ingestion_run`,
- zapisane treningi z `ml.training_run`,
- ranking modeli i metryki,
- na stronie spółki: fakty finansowe i rzeczywiste vs prognozowane wyniki z `ml.prediction`.

## Ważne ograniczenie metodologiczne

Ta wersja ma **pokazać działający przepływ end-to-end na prawdziwych danych internetowych**. Yahoo Finance jest praktycznym źródłem prototypowym, ale nie powinno być jedynym źródłem finalnych danych fundamentalnych ani dat publikacji w pracy inżynierskiej. Finalny dataset powinien zastąpić/zweryfikować fakty i `available_at` przy użyciu raportów emitentów, ESPI/ESEF. Kod i baza są przygotowane do takiej podmiany bez przebudowy modeli lub dashboardu.
