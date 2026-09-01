# v5.4 – zakładka Dane / przygotowanie i jakość danych

Nowa strona: `http://localhost:3000/data`.

Zakładka jest przeznaczona do profesjonalnej prezentacji części danych przed modelowaniem. Pokazuje:
- pełny przebieg ETL i preprocessing,
- zakres czasowy notowań, fundamentów i danych makro,
- pokrycie danych kwartalnych na wykresie,
- liczbę rekordów i okresów per spółka,
- kompletność cech po feature engineering,
- pokrycie konceptów finansowych,
- dostępne serie makro,
- podstawowe kontrole jakości,
- daty proxy +120 dni,
- nierozpoznane etykiety mapowania,
- rekomendacje przed modelowaniem.

Backend udostępnia nowy endpoint: `GET /api/v1/data-preparation`.

Aktualizacja istniejącej instalacji:
```powershell
docker compose down
docker compose build --no-cache api web
docker compose up -d
```

Baza nie wymaga migracji w v5.4. Nie używaj `-v`, jeżeli chcesz zachować pobrane dane.
