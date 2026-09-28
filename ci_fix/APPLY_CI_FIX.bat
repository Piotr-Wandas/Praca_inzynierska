@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================
echo Financial Prediction - v6.3.2 CI / RUFF FIX
echo ============================================================

where docker >nul 2>nul
if errorlevel 1 (
  echo [BLAD] Docker nie jest dostepny w PATH.
  pause
  exit /b 1
)

docker compose ps >nul 2>nul
if errorlevel 1 (
  echo [INFO] Uruchamiam kontenery...
  docker compose up -d --build
  if errorlevel 1 goto :error
)

echo [1/4] Aktualizacja konfiguracji Ruff...
docker compose exec -T api python /app/ci_fix/apply_ruff_config_fix.py
if errorlevel 1 goto :error

echo [2/4] Automatyczna naprawa lintingu...
docker compose exec -T api ruff check src tests apps/api --fix --unsafe-fixes
if errorlevel 1 (
  echo [INFO] Pierwsze przejscie pozostawilo bledy - uruchamiam formatowanie.
)

echo [3/4] Formatowanie kodu...
docker compose exec -T api ruff format src tests apps/api
if errorlevel 1 goto :error

echo [4/4] Kontrola koncowa...
docker compose exec -T api ruff check src tests apps/api
if errorlevel 1 goto :error

echo.
echo [OK] Ruff zakonczony bez bledow.
echo.
echo Teraz wykonaj:
echo   git status
echo   git add .
echo   git commit -m "Fix CI lint errors"
echo   git push
echo.
pause
exit /b 0

:error
echo.
echo [BLAD] Poprawka nie zakonczyla sie poprawnie.
echo Wykonaj:
echo   docker compose exec api ruff check src tests apps/api
echo i zachowaj wynik.
pause
exit /b 1
