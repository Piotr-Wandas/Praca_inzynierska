$ErrorActionPreference = "Stop"
$base = "http://localhost:8000"
$deadline = (Get-Date).AddMinutes(3)
$health = $null
Write-Host "Oczekiwanie na API..."
while ((Get-Date) -lt $deadline) {
  try {
    $health = Invoke-RestMethod -Uri "$base/api/v1/system/health" -TimeoutSec 4
    if ($health.status -eq "ok") { break }
  } catch { }
  Start-Sleep -Seconds 2
}
if (-not $health -or $health.status -ne "ok") {
  Write-Host "BLAD: API nie jest gotowe." -ForegroundColor Red
  exit 10
}

$summary = Invoke-RestMethod -Uri "$base/api/v1/dashboard/summary" -TimeoutSec 10
$modelsUrl = "$base/api/v1/dashboard/models?latest=true&target_code=NET_INCOME_CANONICAL"
$models = Invoke-RestMethod -Uri $modelsUrl -TimeoutSec 10
$review = Invoke-RestMethod -Uri "$base/api/v1/review/info" -TimeoutSec 10

$checks = @(
  @{Name="Spolki"; Value=[int]$summary.companies; Min=1},
  @{Name="Notowania"; Value=[int]$summary.market_rows; Min=1},
  @{Name="Fakty finansowe"; Value=[int]$summary.fundamental_rows; Min=1},
  @{Name="Dane makro"; Value=[int]$summary.macro_rows; Min=1},
  @{Name="Modele"; Value=@($models).Count; Min=1}
)
$failed = $false
foreach ($c in $checks) {
  if ($c.Value -ge $c.Min) {
    Write-Host ("[OK] {0}: {1}" -f $c.Name, $c.Value) -ForegroundColor Green
  } else {
    Write-Host ("[BLAD] {0}: {1}" -f $c.Name, $c.Value) -ForegroundColor Red
    $failed = $true
  }
}
if (-not $review.snapshot.prepared) {
  Write-Host "[BLAD] Snapshot REVIEW nie jest oznaczony jako przygotowany." -ForegroundColor Red
  $failed = $true
}
if ($failed) { exit 20 }
Write-Host "SYSTEM REVIEW GOTOWY" -ForegroundColor Green
exit 0
