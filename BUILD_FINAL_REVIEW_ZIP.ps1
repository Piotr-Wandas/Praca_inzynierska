$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$metaPath = Join-Path $root "review\metadata\snapshot.json"
$dbPath = Join-Path $root "review\database\900-review-data.sql"
$healthPath = Join-Path $root "review\scripts\review_healthcheck.ps1"
$startPath = Join-Path $root "START_REVIEW.bat"
$composePath = Join-Path $root "docker-compose.review.yml"

function Require-File([string]$Path, [string]$Label, [long]$MinBytes = 1) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Brak: $Label ($Path)" }
    $len = (Get-Item -LiteralPath $Path).Length
    if ($len -lt $MinBytes) { throw "$Label jest podejrzanie maly: $len bajtow" }
    Write-Host ("[OK] {0}: {1} bajtow" -f $Label, $len) -ForegroundColor Green
}

Write-Host "Walidacja snapshotu przed budowa paczki..." -ForegroundColor Cyan
Require-File $metaPath "snapshot metadata" 20
Require-File $dbPath "PostgreSQL dump" 1000
Require-File $healthPath "review healthcheck" 100
Require-File $startPath "START_REVIEW.bat" 100
Require-File $composePath "docker-compose.review.yml" 50

$meta = Get-Content -LiteralPath $metaPath -Raw | ConvertFrom-Json
if ($meta.prepared -ne $true) { throw "Snapshot REVIEW nie jest oznaczony jako prepared=true." }
if ([int]$meta.companies -lt 1) { throw "Snapshot nie zawiera spolek." }
if ([int]$meta.market_rows -lt 1) { throw "Snapshot nie zawiera notowan." }
if ([int]$meta.fundamental_rows -lt 1) { throw "Snapshot nie zawiera faktow finansowych." }
if ([int]$meta.macro_rows -lt 1) { throw "Snapshot nie zawiera danych makro." }
if ([int]$meta.model_runs -lt 1) { throw "Snapshot nie zawiera wynikow modeli." }
Write-Host ("[OK] Snapshot: spolki={0}, notowania={1}, fakty={2}, makro={3}, modele={4}" -f $meta.companies,$meta.market_rows,$meta.fundamental_rows,$meta.macro_rows,$meta.model_runs) -ForegroundColor Green

$out = Join-Path (Split-Path -Parent $root) "Financial_Prediction_v6_3_1_FINAL_REVIEW.zip"
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }
$stage = Join-Path $env:TEMP ("fp_review_" + [guid]::NewGuid().ToString("N"))
$verify = Join-Path $env:TEMP ("fp_verify_" + [guid]::NewGuid().ToString("N"))
$dest = Join-Path $stage "Financial_Prediction_v6_3_1_FINAL_REVIEW"
New-Item -ItemType Directory -Path $dest -Force | Out-Null

try {
    $exclude = @(".git", ".venv", "node_modules", ".next", "__pycache__", ".env")
    Get-ChildItem -LiteralPath $root -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $dest -Recurse -Force
    }

    # Walidacja stagingu - ten sam JSON, ktory odczyta START_REVIEW.
    $stagedMeta = Join-Path $dest "review\metadata\snapshot.json"
    $stagedDb = Join-Path $dest "review\database\900-review-data.sql"
    Require-File $stagedMeta "staged snapshot metadata" 20
    Require-File $stagedDb "staged PostgreSQL dump" 1000
    $sm = Get-Content -LiteralPath $stagedMeta -Raw | ConvertFrom-Json
    if ($sm.prepared -ne $true -or [int]$sm.model_runs -lt 1) { throw "Snapshot w stagingu jest niepoprawny." }

    Compress-Archive -LiteralPath $dest -DestinationPath $out -CompressionLevel Optimal
    Require-File $out "FINAL REVIEW ZIP" 1000

    # Najwazniejsza kontrola: rozpakowujemy gotowy ZIP i ponownie sprawdzamy snapshot.
    New-Item -ItemType Directory -Path $verify -Force | Out-Null
    Expand-Archive -LiteralPath $out -DestinationPath $verify -Force
    $unpackedRoot = Join-Path $verify "Financial_Prediction_v6_3_1_FINAL_REVIEW"
    $unpackedMeta = Join-Path $unpackedRoot "review\metadata\snapshot.json"
    $unpackedDb = Join-Path $unpackedRoot "review\database\900-review-data.sql"
    Require-File $unpackedMeta "ZIP snapshot metadata" 20
    Require-File $unpackedDb "ZIP PostgreSQL dump" 1000
    $um = Get-Content -LiteralPath $unpackedMeta -Raw | ConvertFrom-Json
    if ($um.prepared -ne $true -or [int]$um.model_runs -lt 1) { throw "Snapshot po rozpakowaniu ZIP jest niepoprawny." }

    Write-Host "" 
    Write-Host "[OK] FINAL REVIEW przeszedl walidacje przed i po spakowaniu." -ForegroundColor Green
    Write-Host "Gotowa paczka: $out" -ForegroundColor Green
} finally {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $verify) { Remove-Item -LiteralPath $verify -Recurse -Force -ErrorAction SilentlyContinue }
}
