# v5.6 — interaktywny podgląd danych

Dodano zakładkę `/data-browser`, która pozwala użytkownikowi zobaczyć rzeczywiste rekordy wykorzystywane przez system.

## Obsługiwane zbiory
- notowania dzienne (`core.daily_price`),
- dane fundamentalne (`core.financial_fact` + kanoniczne koncepty),
- dane makroekonomiczne (`core.macro_observation`),
- dataset modelowy po point-in-time join i feature engineering.

## Funkcje
- filtrowanie po spółce, koncepcie, serii i zakresie dat,
- wyszukiwanie tekstowe,
- sortowanie przez kliknięcie nagłówka kolumny,
- paginacja 25/50/100/200 rekordów,
- opcjonalny podgląd historycznych wersji faktów,
- filtr rekordów datasetu modelowego ze znanym targetem,
- eksport aktualnie widocznej strony do CSV,
- wyraźne oznaczanie wartości NULL.

Zapytania są wykonywane po stronie API/PostgreSQL. Użytkownik nie przekazuje własnego SQL, a kolumny sortowania są ograniczone whitelistą.

## Aktualizacja
```
docker compose down
docker compose build --no-cache api web
docker compose up -d
```
Nie trzeba kasować bazy ani ponownie pobierać danych.
