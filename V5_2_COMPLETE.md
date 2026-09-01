# Financial Prediction Platform v5.2

Wersja v5.2 poprawia problemy ujawnione po pierwszym treningu na dłuższej historii danych.

## Najważniejsze zmiany

1. **Kanoniczny target zysku netto**
   - preferowany: `NET_INCOME_PARENT`,
   - fallback: `NET_INCOME`, gdy źródło nie rozróżnia zysku przypisanego akcjonariuszom jednostki dominującej,
   - w datasetcie zachowywana jest informacja `net_income_source` oraz `target_source_concept`.

2. **Szersze mapowanie nazw pozycji finansowych Bankier.pl**
   - zysk netto,
   - zysk netto jednostki dominującej,
   - przychody,
   - wynik operacyjny,
   - aktywa,
   - kapitał własny,
   - wynik odsetkowy,
   - wynik prowizyjny,
   - cash flow operacyjny.

3. **Poprawiony identyfikator Dino Polska**
   - Bankier slug: `DINOPL` zamiast `DINO`.

4. **Bezpieczna aktualizacja starej bazy v5.1**
   - podczas ponownego ingestu stare bieżące rekordy Bankier dla danego zakresu są dezaktywowane (`is_current=false`),
   - historia wersji nie jest kasowana,
   - nowe koncepty `NET_INCOME` i `NET_FEE_INCOME` są dodawane automatycznie także bez kasowania wolumenu PostgreSQL.

5. **Wspólny zbiór ewaluacyjny**
   - każdy model jest oceniany na tych samych obserwacjach,
   - wspólna próbka wymaga targetu, `net_income_lag1` i `net_income_lag4`,
   - Seasonal baseline, Last value, Ridge, Random Forest i HistGradientBoosting mają identyczną liczbę rekordów OOF,
   - kod przerywa trening, jeśli wykryje różne liczby obserwacji między modelami.

6. **Metryki liczone globalnie z predykcji OOF**
   - MAE,
   - RMSE,
   - MedAE,
   - sMAPE,
   - WAPE,
   - R²,
   - liczba obserwacji,
   - liczba foldów,
   - liczba spółek,
   - zakres ewaluacji.

7. **Jedna wersja datasetu dla całego eksperymentu**
   - wszystkie modele z pojedynczego treningu mają wspólny `dataset_version_id`,
   - dashboard nie miesza wyników ze starych eksperymentów,
   - champion jest wybierany tylko z najnowszej wersji datasetu.

8. **Rozszerzony dashboard**
   - pokrycie targetu,
   - liczba obserwacji wspólnej próbki OOF,
   - udział `NET_INCOME_PARENT` i fallback `NET_INCOME`,
   - kompletność cech,
   - gotowość lag4,
   - źródła fundamentów,
   - porównanie modeli na wspólnej próbce,
   - MAE/RMSE championa per spółka,
   - diagnostyka per kwartał na ekranie `/models`.

## Aktualizacja z v5.1

Nie kasuj bazy, jeżeli chcesz zachować dotychczasowe rekordy.

```powershell
docker compose down
docker compose build --no-cache api web
docker compose up -d
```

Zalecane jest ponowne uruchomienie idempotentnego skryptu bazy:

```powershell
docker compose exec api python scripts/init_database.py
```

## Ponowne pobranie fundamentów

Najpierw pilot 5 spółek:

```powershell
docker compose exec api python scripts/ingest_internet_data.py --start-year 2018 --tickers PKO PEO ORL CDR DNP
```

Skrypt automatycznie dezaktywuje wcześniejsze bieżące mapowania Bankier dla ponownie pobieranego zakresu, więc stare błędne mapowanie `NET_INCOME_PARENT` nie powinno pozostać jako bieżące.

## Raport jakości

```powershell
docker compose exec api python scripts/data_quality_report.py
```

W v5.2 zwróć uwagę przede wszystkim na:

- `target_coverage`,
- `common_eval_rows`,
- `common_eval_companies`,
- `common_eval_periods`,
- `target_provenance.parent_targets`,
- `target_provenance.generic_fallback_targets`.

## Trening

```powershell
docker compose exec api python scripts/train_from_database.py
```

Każdy model powinien mieć identyczne `n_obs` / `evaluation_observations`.

## Aplikacja

- Dashboard: http://localhost:3000/dashboard
- Modele: http://localhost:3000/models
- Spółki: http://localhost:3000/companies
- FastAPI: http://localhost:8000/docs

## Ważne metodologicznie

Bankier i Yahoo pozostają agregacyjnymi źródłami prototypowymi. Jeżeli `source_label` zawiera `availability_proxy_120d`, data dostępności nie jest rzeczywistą datą publikacji. Przed finalnym eksperymentem do pracy inżynierskiej należy zweryfikować wartości oraz `available_at` w raportach emitentów/ESPI/ESEF.
