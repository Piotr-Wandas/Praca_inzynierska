@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Financial Prediction - REVIEW v6.3.1

echo ==========================================================
echo   Financial Prediction - v6.3.1 FINAL REVIEW FIX
echo ==========================================================
echo.

where docker >nul 2>nul
if errorlevel 1 (
  echo [BLAD] Nie znaleziono polecenia Docker.
  echo Zainstaluj i uruchom Docker Desktop, a potem sproboj ponownie.
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo [BLAD] Docker Desktop nie jest uruchomiony.
  echo Uruchom Docker Desktop i poczekaj, az silnik bedzie gotowy.
  pause
  exit /b 2
)

REM Nie uzywamy FINDSTR do JSON. PowerShell faktycznie parsuje snapshot.json.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $p=Join-Path (Get-Location) 'review\metadata\snapshot.json'; if(-not (Test-Path -LiteralPath $p)){exit 11}; $m=Get-Content -LiteralPath $p -Raw | ConvertFrom-Json; if($m.prepared -ne $true){exit 12}; if([int]$m.model_runs -lt 1){exit 13}; exit 0"
if errorlevel 1 (
  echo [BLAD] Paczka nie zawiera poprawnego, przygotowanego snapshotu REVIEW.
  echo Oczekiwany plik: review\metadata\snapshot.json
  echo Autor powinien uruchomic PREPARE_REVIEW_SNAPSHOT.bat, a potem BUILD_FINAL_REVIEW_ZIP.bat.
  pause
  exit /b 3
)

if not exist "review\database\900-review-data.sql" (
  echo [BLAD] Brak dumpu bazy review\database\900-review-data.sql
  pause
  exit /b 4
)
for %%F in ("review\database\900-review-data.sql") do if %%~zF LSS 1000 (
  echo [BLAD] Dump bazy jest pusty lub podejrzanie maly: %%~zF bajtow.
  pause
  exit /b 5
)

if not exist "review\scripts\review_healthcheck.ps1" (
  echo [BLAD] Brak skryptu review_healthcheck.ps1.
  pause
  exit /b 6
)

echo [1/4] Przygotowanie czystego srodowiska REVIEW...
REM Usuwamy tylko wolumeny tego projektu, aby import dumpu wykonal sie od zera.
docker compose -f docker-compose.yml -f docker-compose.review.yml down -v --remove-orphans >nul 2>nul

echo [2/4] Uruchamianie kontenerow i odtwarzanie snapshotu...
docker compose -f docker-compose.yml -f docker-compose.review.yml up -d --build
if errorlevel 1 goto :fail

echo [3/4] Kontrola API, bazy, snapshotu i modeli...
powershell -NoProfile -ExecutionPolicy Bypass -File review\scripts\review_healthcheck.ps1
if errorlevel 1 goto :fail

echo [4/4] Otwieranie aplikacji...
start "" "http://localhost:3000/review"

echo.
echo ==========================================================
echo   SYSTEM REVIEW GOTOWY
echo   Aplikacja: http://localhost:3000
echo   Tryb REVIEW: http://localhost:3000/review
echo   Dane:       http://localhost:3000/data-browser
echo   Analizy:    http://localhost:3000/analytics
echo   Modele:     http://localhost:3000/models
echo   API:        http://localhost:8000/docs
echo   MLflow:     http://localhost:5000
echo ==========================================================
echo.
pause
exit /b 0

:fail
echo.
echo [BLAD] Nie udalo sie uruchomic wersji REVIEW.
echo Sprawdz logi poleceniem: docker compose -f docker-compose.yml -f docker-compose.review.yml logs --tail=200
pause
exit /b 10
