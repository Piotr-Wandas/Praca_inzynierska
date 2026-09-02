$ErrorActionPreference = "Stop"

Write-Host "Uruchamianie demonstracyjnego pipeline ML..."
python -m financial_platform.modeling.demo_pipeline

Write-Host "Uruchamianie testow..."
python -m pytest -q

Write-Host "Demo zakonczone. Wyniki sa wylacznie testowe/syntetyczne."
