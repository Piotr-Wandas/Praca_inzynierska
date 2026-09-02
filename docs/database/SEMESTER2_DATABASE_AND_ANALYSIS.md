# Database and analysis package — semester II

This package is intentionally split into two parallel mechanisms:

1. `sql/create_database.sql` — readable SQL artifact for the thesis assessment. It explicitly shows schemas, tables, keys, constraints and indexes.
2. Alembic migrations — application-side schema evolution mechanism used by the Python project.

The SQL file is not a replacement for Alembic; it is a transparent database-design artifact suitable for the Database specialization.

## Database layers

- `metadata` — data-source lineage, ingestion runs, quality checks,
- `raw` — reserved for source-faithful raw data,
- `staging` — technical cleaning and type normalization,
- `core` — canonical business model,
- `analytics` — views and analytical projections,
- `ml` — dataset/model/experiment/prediction metadata,
- `app` — application-facing data if needed later.

## Current semester-II analysis

The runnable analysis uses the synthetic demonstration panel in `data/demo/panel_demo.csv` only to prove that the software pipeline works. It must not be presented as empirical research results.

The code currently contains:

- point-in-time validation,
- deterministic data cleaning,
- financial lag features,
- market feature functions,
- macro lag functions,
- two naive baselines,
- Ridge regression,
- Random Forest,
- Histogram Gradient Boosting,
- chronological walk-forward validation,
- MAE, RMSE, MedAE, sMAPE, WAPE and R²,
- optional MLflow logging,
- CSV export of fold-level metrics and model ranking.

## Run the database script

If PostgreSQL is exposed by Docker on localhost:5432:

```powershell
$env:PGPASSWORD="change_me"
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="financial_platform"
$env:PGUSER="fp_app"
psql -v ON_ERROR_STOP=1 -f .\sql\create_database.sql
psql -v ON_ERROR_STOP=1 -f .\sql\views\analytics_views.sql
```

If `psql` is unavailable locally, execute the scripts inside the PostgreSQL container instead.

## Run the analysis

```powershell
.\.venv\Scripts\Activate.ps1
python .\scripts\run_analysis.py
```

Outputs:

- `artifacts/semester2_analysis/fold_metrics.csv`
- `artifacts/semester2_analysis/model_comparison.csv`

## What still belongs to the next implementation step

Real WIG20 results require replacing the synthetic panel with a point-in-time dataset generated from actual GPW/issuer/NBP/GUS data. This package deliberately does not fabricate those results.
