# Checklist v5.3 DATA FIX

Po aktualizacji wykonaj kolejno:

```powershell
docker compose down
docker compose build --no-cache api web
docker compose up -d
docker compose exec api python scripts/init_database.py
```

Następnie:

```powershell
docker compose exec api python scripts/ingest_internet_data.py --start-year 2018 --tickers PKO PEO ORL CDR DNP
docker compose exec api python scripts/mapping_audit_report.py
docker compose exec api python scripts/data_quality_report.py
```

Jeżeli wspólna próbka OOF dla `net_income` ma co najmniej 20 obserwacji:

```powershell
docker compose exec api python scripts/train_from_database.py --target net_income
```

Target kontrolny:

```powershell
docker compose exec api python scripts/train_from_database.py --target revenue
```

Dashboard: `http://localhost:3000/dashboard`
Swagger: `http://localhost:8000/docs`
