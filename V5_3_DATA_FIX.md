# Financial Prediction Platform v5.3 DATA FIX

Wersja v5.3 koncentruje się na problemie ujawnionym przez dashboard v5.2: długa historia finansowa była obecna w bazie, ale pokrycie `NET_INCOME` i wspólnej próbki OOF pozostawało niskie. Przyczyną były przede wszystkim różnice w nazewnictwie wierszy źródłowych oraz brak jawnego audytu mapowania.

## Najważniejsze zmiany

1. **Audyt surowych etykiet Bankier/Notoria**
   - nowa tabela `staging.financial_mapping_audit`,
   - każdy wiersz źródłowy jest zapisany wraz z decyzją mapowania, pewnością, metodą, liczbą wartości i zakresem dat,
   - nierozpoznane wiersze nie są automatycznie przypisywane do przypadkowego konceptu.

2. **Mapowanie oparte na faktycznych etykietach**
   - obsługa m.in. `Zysk/strata netto udziałowców jednostki dominującej`,
   - obsługa `Zysk/strata netto`,
   - obsługa `Przychody z podstawowej działalności operacyjnej`,
   - wykluczenie `udziałowców niekontrolujących` i `działalności zaniechanej`,
   - bezpieczne reguły dla wyniku operacyjnego, EBITDA, aktywów, kapitału własnego, wyniku odsetkowego i prowizyjnego.

3. **Lepsze pobieranie tabel**
   - parser próbuje wariant skonsolidowany, stronę domyślną i jednostkowy,
   - wybiera wariant z najdłuższą historią kwartalną,
   - zachowuje rzeczywiste daty publikacji z tabel, jeśli parser może je odczytać; `+120 dni` pozostaje oznaczonym fallbackiem.

4. **Trzy targety**
   - `net_income` → `NET_INCOME_CANONICAL` dla całego panelu,
   - `revenue` → `REVENUE` dla spółek niefinansowych,
   - `net_interest_income` → `NET_INTEREST_INCOME` dla sektora finansowego.

5. **Rygorystyczna wspólna ewaluacja**
   - wszystkie modele są porównywane na identycznej próbce OOF,
   - domyślnie trening wymaga co najmniej 20 wspólnych obserwacji,
   - dashboard uznaje zysk netto za gotowy do interpretacji dopiero przy: pokryciu targetu >= 50%, OOF >= 40, co najmniej 8 okresach i 4 spółkach.

6. **Dashboard DATA FIX**
   - gotowość każdego targetu,
   - skuteczność mapowania etykiet,
   - lista najważniejszych nierozpoznanych etykiet zawierających wartości,
   - pokrycie feature engineering,
   - wspólna próbka OOF i diagnostyka modeli.

## Aktualizacja istniejącej bazy v5.2

Nie usuwaj wolumenu PostgreSQL. Po rozpakowaniu v5.3:

```powershell
docker compose down
docker compose build --no-cache api web
docker compose up -d
docker compose exec api python scripts/init_database.py
```

`init_database.py` doda tabelę audytu do istniejącej bazy.

## Zalecana kolejność uruchomienia

Najpierw ponownie pobierz pięć spółek pilotażowych:

```powershell
docker compose exec api python scripts/ingest_internet_data.py --start-year 2018 --tickers PKO PEO ORL CDR DNP
```

Następnie sprawdź audyt mapowania:

```powershell
docker compose exec api python scripts/mapping_audit_report.py
```

Pełny raport jakości:

```powershell
docker compose exec api python scripts/data_quality_report.py
```

Dopiero potem uruchom model zysku netto:

```powershell
docker compose exec api python scripts/train_from_database.py --target net_income
```

Target kontrolny dla spółek niefinansowych:

```powershell
docker compose exec api python scripts/train_from_database.py --target revenue
```

Target sektorowy dla banków:

```powershell
docker compose exec api python scripts/train_from_database.py --target net_interest_income
```

Jeżeli świadomie chcesz wykonać techniczny test na mniejszej próbce, możesz zmienić minimalną liczbę OOF, np.:

```powershell
docker compose exec api python scripts/train_from_database.py --target net_income --min-common-eval-rows 10
```

Nie należy jednak interpretować takiego rankingu jako finalnego wyniku badawczego.

## Dashboard

- aplikacja: `http://localhost:3000`
- dashboard: `http://localhost:3000/dashboard`
- modele: `http://localhost:3000/models`
- FastAPI: `http://localhost:8000/docs`

## Ważne metodologicznie

Bankier/Notoria i Yahoo są źródłami agregacyjnymi używanymi do budowy prototypu. Przed raportowaniem finalnych wyników pracy wartości fundamentalne i dokładne daty `available_at` należy zweryfikować w raportach emitentów / ESPI / ESEF.
