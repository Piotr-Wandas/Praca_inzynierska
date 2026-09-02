@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Przygotowanie snapshotu REVIEW v6.0.1

echo ==========================================================
echo   PREPARE REVIEW SNAPSHOT - v6.0.1 - tylko dla autora pracy
echo ==========================================================
echo.
echo Skrypt eksportuje AKTUALNA baze i artefakty modeli.
echo Przed uruchomieniem upewnij sie, ze dane i treningi sa finalne.
echo.

where docker >nul 2>nul || (echo [BLAD] Brak Docker.& pause & exit /b 1)
docker info >nul 2>nul || (echo [BLAD] Docker Desktop nie dziala.& pause & exit /b 2)

docker compose up -d postgres api >nul
if errorlevel 1 (echo [BLAD] Nie mozna uruchomic postgres/api.& pause & exit /b 3)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=(Get-Date).AddMinutes(2); do { try {$h=Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/system/health' -TimeoutSec 3 -ErrorAction Stop} catch {$h=$null}; if($h.status -eq 'ok'){exit 0}; Start-Sleep 2 } while((Get-Date)-lt $d); exit 1"
if errorlevel 1 (echo [BLAD] API nie jest gotowe.& pause & exit /b 4)

REM Pobieramy statystyki. URL modeli jest budowany w PowerShell,
REM aby znak & nie byl interpretowany przez parser pliku BAT.
for /f %%A in ('powershell -NoProfile -Command "$ErrorActionPreference='Stop'; try { [int](Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/dashboard/summary').companies } catch { exit 1 }"') do set COMPANIES=%%A
for /f %%A in ('powershell -NoProfile -Command "$ErrorActionPreference='Stop'; try { [int](Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/dashboard/summary').market_rows } catch { exit 1 }"') do set MARKET=%%A
for /f %%A in ('powershell -NoProfile -Command "$ErrorActionPreference='Stop'; try { [int](Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/dashboard/summary').fundamental_rows } catch { exit 1 }"') do set FUND=%%A
for /f %%A in ('powershell -NoProfile -Command "$ErrorActionPreference='Stop'; try { [int](Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/dashboard/summary').macro_rows } catch { exit 1 }"') do set MACRO=%%A
for /f %%A in ('powershell -NoProfile -Command "$ErrorActionPreference='Stop'; try { $u='http://localhost:8000/api/v1/dashboard/models?latest=true'+[char]38+'target_code=NET_INCOME_CANONICAL'; @((Invoke-RestMethod -Uri $u)).Count } catch { Write-Error $_; exit 1 }"') do set MODELS=%%A

if not defined COMPANIES goto :readerror
if not defined MARKET goto :readerror
if not defined FUND goto :readerror
if not defined MACRO goto :readerror
if not defined MODELS goto :readerror

if "%COMPANIES%"=="0" goto :nodata
if "%MARKET%"=="0" goto :nodata
if "%FUND%"=="0" goto :nodata
if "%MACRO%"=="0" goto :nodata
if "%MODELS%"=="0" goto :nodata

if not exist review\database mkdir review\database
if not exist review\metadata mkdir review\metadata
if exist review\artifacts rmdir /s /q review\artifacts
mkdir review\artifacts

echo [1/4] Eksport danych PostgreSQL...
REM --disable-triggers zabezpiecza odtworzenie data-only dump przy cyklicznych FK.
docker compose exec -T postgres sh -lc "pg_dump -U $POSTGRES_USER -d $POSTGRES_DB --data-only --disable-triggers --no-owner --no-privileges --exclude-table-data=core.market_index --exclude-table-data=core.financial_concept" > review\database\900-review-data.sql
if errorlevel 1 (echo [BLAD] pg_dump nie udal sie.& pause & exit /b 5)

for %%F in (review\database\900-review-data.sql) do if %%~zF LSS 1000 (
  echo [BLAD] Dump bazy jest podejrzanie maly: %%~zF bajtow.
  pause
  exit /b 5
)

echo [2/4] Eksport artefaktow modeli...
docker compose cp api:/app/artifacts/. review\artifacts\ >nul 2>nul
if errorlevel 1 echo [UWAGA] Nie udalo sie skopiowac wszystkich artefaktow; metryki i predykcje nadal sa w bazie.

echo [3/4] Tworzenie metadanych snapshotu...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { $s=Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/dashboard/summary'; $u='http://localhost:8000/api/v1/dashboard/models?latest=true'+[char]38+'target_code=NET_INCOME_CANONICAL'; $m=Invoke-RestMethod -Uri $u; $o=[ordered]@{prepared=$true; release='v6.0.1 REVIEW RELEASE'; created_at=(Get-Date).ToString('o'); companies=[int]$s.companies; market_rows=[int]$s.market_rows; fundamental_rows=[int]$s.fundamental_rows; macro_rows=[int]$s.macro_rows; model_runs=@($m).Count; dataset_version=if($s.dataset_version){$s.dataset_version.version_code}else{$null}; note='Snapshot utworzony z lokalnej, zweryfikowanej bazy autora.'}; $json=$o|ConvertTo-Json -Depth 6; [System.IO.File]::WriteAllText((Join-Path (Get-Location) 'review\metadata\snapshot.json'),$json,(New-Object System.Text.UTF8Encoding($false))); exit 0 } catch { Write-Error $_; exit 1 }"
if errorlevel 1 (echo [BLAD] Nie zapisano metadata. Snapshot NIE jest gotowy.& pause & exit /b 6)

powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $m=Get-Content -Raw 'review\metadata\snapshot.json'|ConvertFrom-Json; if(-not $m.prepared -or [int]$m.model_runs -lt 1){exit 1}else{exit 0}"
if errorlevel 1 (echo [BLAD] Walidacja snapshot.json nie powiodla sie.& pause & exit /b 7)

echo [4/4] Snapshot przygotowany i zweryfikowany.
echo Spolki: %COMPANIES%
echo Notowania: %MARKET%
echo Fakty: %FUND%
echo Makro: %MACRO%
echo Modele: %MODELS%
echo.
echo Teraz uruchom BUILD_FINAL_REVIEW_ZIP.bat.
pause
exit /b 0

:readerror
echo [BLAD] Nie udalo sie pobrac statystyk z API.
echo Nie utworzono gotowego snapshotu. Sprawdz http://localhost:8000/docs i logi API.
pause
exit /b 19

:nodata
echo [BLAD] Baza nie jest gotowa do snapshotu.
echo Spolki=%COMPANIES% Rynek=%MARKET% Fakty=%FUND% Makro=%MACRO% Modele=%MODELS%
echo Najpierw pobierz dane i wykonaj trening modeli.
pause
exit /b 20
