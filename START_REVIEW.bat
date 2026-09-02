@echo off
setlocal
cd /d "%~dp0"
title Financial Prediction - REVIEW

echo ==========================================================
echo   Financial Prediction - v6.0.1 REVIEW RELEASE
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

findstr /C:"\"prepared\": true" review\metadata\snapshot.json >nul 2>nul
if errorlevel 1 (
  echo [BLAD] Paczka nie zawiera przygotowanego snapshotu REVIEW.
  echo Autor pracy powinien najpierw uruchomic PREPARE_REVIEW_SNAPSHOT.bat
  echo na komputerze z uzupelniona baza i wynikami modeli, a nastepnie
  echo przekazac wygenerowana paczke FINAL REVIEW.
  pause
  exit /b 3
)

echo [1/4] Uruchamianie kontenerow...
docker compose -f docker-compose.yml -f docker-compose.review.yml up -d --build
if errorlevel 1 goto :fail

echo [2/4] Kontrola API, bazy i modeli...
powershell -NoProfile -ExecutionPolicy Bypass -File review\scripts\review_healthcheck.ps1
if errorlevel 1 goto :fail

echo [3/4] System gotowy.
echo [4/4] Otwieranie aplikacji...
start "" "http://localhost:3000/review"

echo.
echo ==========================================================
echo   SYSTEM GOTOWY
echo   Aplikacja: http://localhost:3000
echo   Tryb REVIEW: http://localhost:3000/review
echo   Dane:       http://localhost:3000/data-browser
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
echo Sprawdz logi poleceniem: docker compose logs --tail=200
pause
exit /b 10
