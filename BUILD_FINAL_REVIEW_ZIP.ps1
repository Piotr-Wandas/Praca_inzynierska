$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$metaPath = Join-Path $root "review\metadata\snapshot.json"
$meta = Get-Content $metaPath -Raw | ConvertFrom-Json
if (-not $meta.prepared) { throw "Snapshot REVIEW nie jest przygotowany. Uruchom PREPARE_REVIEW_SNAPSHOT.bat." }
$out = Join-Path (Split-Path -Parent $root) "Financial_Prediction_v6_0_2_REVIEW_READY.zip"
if (Test-Path $out) { Remove-Item $out -Force }
$stage = Join-Path $env:TEMP ("fp_review_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $stage | Out-Null
$dest = Join-Path $stage "Financial_Prediction_v6_0_2_REVIEW"
New-Item -ItemType Directory -Path $dest | Out-Null
$exclude = @(".git", ".venv", "node_modules", ".next", "__pycache__", ".env")
Get-ChildItem -LiteralPath $root -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
  Copy-Item $_.FullName -Destination $dest -Recurse -Force
}
Compress-Archive -Path $dest -DestinationPath $out -CompressionLevel Optimal
Remove-Item $stage -Recurse -Force
Write-Host "Gotowa paczka: $out" -ForegroundColor Green
