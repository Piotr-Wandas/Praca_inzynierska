$ErrorActionPreference = "Stop"

if (-not $env:PGHOST) { $env:PGHOST = "localhost" }
if (-not $env:PGPORT) { $env:PGPORT = "5432" }
if (-not $env:PGDATABASE) { $env:PGDATABASE = "financial_platform" }
if (-not $env:PGUSER) { $env:PGUSER = "fp_app" }

Write-Host "Creating thesis database schema in $($env:PGDATABASE) on $($env:PGHOST):$($env:PGPORT)..."
psql -v ON_ERROR_STOP=1 -f "sql/create_database.sql"
psql -v ON_ERROR_STOP=1 -f "sql/views/analytics_views.sql"
Write-Host "Database schema created successfully."
