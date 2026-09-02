@echo off
cd /d "%~dp0"
echo UWAGA: reset usunie lokalne wolumeny REVIEW i przywroci snapshot przy kolejnym starcie.
choice /C TN /M "Czy kontynuowac"
if errorlevel 2 exit /b 0
docker compose -f docker-compose.yml -f docker-compose.review.yml down -v
if errorlevel 1 exit /b 1
call START_REVIEW.bat
