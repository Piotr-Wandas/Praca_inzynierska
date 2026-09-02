# v6.0.2 REVIEW BUILD PATH HOTFIX

Poprawka błędu BUILD_FINAL_REVIEW_ZIP.ps1.

W v6.0.1 użyto:

```powershell
$root = Split-Path -Parent $PSScriptRoot
```

co powodowało szukanie `review\metadata\snapshot.json` o jeden katalog za wysoko.

W v6.0.2 użyto:

```powershell
$root = $PSScriptRoot
```

Po poprawnym wykonaniu `PREPARE_REVIEW_SNAPSHOT.bat` wystarczy uruchomić `BUILD_FINAL_REVIEW_ZIP.bat`. Nie trzeba ponownie pobierać danych ani trenować modeli.
