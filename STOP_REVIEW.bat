@echo off
cd /d "%~dp0"
echo Zatrzymywanie Financial Prediction REVIEW...
docker compose -f docker-compose.yml -f docker-compose.review.yml down
echo Gotowe. Dane w wolumenach nie zostaly usuniete.
pause
