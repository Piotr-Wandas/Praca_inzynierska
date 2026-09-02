@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File BUILD_FINAL_REVIEW_ZIP.ps1
if errorlevel 1 (
  echo [BLAD] Nie utworzono paczki finalnej.
  pause
  exit /b 1
)
pause
