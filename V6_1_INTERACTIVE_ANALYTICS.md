# v6.1 — INTERACTIVE ANALYTICS REVIEW

Nowa zakładka `/analytics` udostępnia interaktywny dashboard analityczny oparty bezpośrednio na danych zapisanych w PostgreSQL.

## Filtry
- target: zysk netto, przychody, wynik odsetkowy (jeżeli istnieją treningi),
- model lub automatyczny champion,
- sektor,
- spółka,
- zakres dat.

## Widoki
- KPI dla aktualnie wybranego podzbioru: n, MAE, RMSE, sMAPE, WAPE/R²,
- actual vs predicted w czasie,
- ranking błędu MAE per spółka,
- porównanie modeli na zapisanej wspólnej próbce,
- scatter actual vs predicted,
- feature importance (jeżeli zostało zapisane dla treningu),
- stabilność błędu per okres walk-forward,
- tabela rekordów predykcyjnych użytych w analizie.

## Backend
Dodano endpointy:
- `GET /api/v1/analytics/catalog`
- `GET /api/v1/analytics/overview`

Filtrowanie wykonywane jest po stronie PostgreSQL/FastAPI. Frontend nie używa danych demo.

## Uruchomienie
Po aktualizacji obrazu:

```powershell
docker compose down
docker compose build --no-cache api web
docker compose up -d
```

Następnie otwórz `http://localhost:3000/analytics`.
