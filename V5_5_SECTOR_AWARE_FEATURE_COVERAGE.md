# v5.5 — Sector-aware feature coverage

Ta wersja poprawia interpretację braków danych i sposób wyboru cech do modeli.

## Co zmieniono

1. Każda cecha ma jawny zakres zastosowania: `all`, `financial` albo `non_financial`.
2. Pokrycie cech sektorowych jest liczone względem właściwej populacji, a nie całego panelu.
3. Dashboard pokazuje jednocześnie pokrycie właściwe (scoped coverage) i pomocniczo pokrycie globalne.
4. Dla globalnego modelu zysku netto cechy sektorowe są wyłączane, zamiast imputować wartości bankowe spółkom niefinansowym i odwrotnie.
5. Dla targetu `revenue` używane są cechy globalne + niefinansowe.
6. Dla targetu `net_interest_income` używane są cechy globalne + finansowe.
7. Nadal działa dynamiczne odrzucanie cech z niewystarczającą liczbą obserwacji w konkretnym foldzie walk-forward.

## Dlaczego to jest ważne

Brak `NET_INTEREST_INCOME` dla spółki przemysłowej nie jest klasycznym brakiem danych. Ta cecha po prostu nie ma dla tej spółki zastosowania. v5.5 rozróżnia brak strukturalny od rzeczywistej niekompletności danych.

## Aktualizacja

```powershell
docker compose down
docker compose build --no-cache api web
docker compose up -d
```

Nie trzeba usuwać wolumenu PostgreSQL ani ponownie pobierać danych.

Po uruchomieniu otwórz:

- http://localhost:3000/data
- http://localhost:3000/dashboard
- http://localhost:8000/docs

Przed ponownym treningiem można sprawdzić jakość:

```powershell
docker compose exec api python scripts/data_quality_report.py
```

Trening zysku netto:

```powershell
docker compose exec api python scripts/train_from_database.py --target net_income
```
