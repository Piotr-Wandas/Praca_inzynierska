# v6.0.1 REVIEW RELEASE — hotfix przygotowania snapshotu

Poprawiono dwa problemy zauważone podczas `PREPARE_REVIEW_SNAPSHOT.bat`:

1. **`latest=true^` wysyłane do FastAPI** — znak `&` w adresie URL był niepoprawnie escapowany w pliku BAT i do parametru logicznego `latest` trafiała wartość `true^`. Adres modeli jest teraz składany wewnątrz PowerShell (`[char]38`), więc FastAPI otrzymuje poprawne `latest=true&target_code=...`.
2. **Odtwarzanie data-only dump z cyklicznymi FK** — `pg_dump` korzysta teraz z `--disable-triggers`, aby snapshot danych mógł zostać bezpiecznie odtworzony na pustej bazie REVIEW.

Dodatkowo przygotowanie snapshotu przerywa się, jeśli:
- nie uda się odczytać statystyk z API,
- liczba modeli jest równa zero,
- dump ma podejrzanie mały rozmiar,
- `snapshot.json` nie zostanie poprawnie utworzony lub zweryfikowany.

## Aktualizacja

Nie trzeba pobierać danych ani trenować modeli ponownie. Zachowaj istniejące wolumeny Docker i wykonaj:

```powershell
docker compose down
docker compose build --no-cache api web
docker compose up -d
```

Następnie:

```text
PREPARE_REVIEW_SNAPSHOT.bat
```

Po poprawnym wykonaniu powinieneś zobaczyć liczbową wartość `Modele`, np. `Modele: 5`, bez czerwonego błędu FastAPI.

Na końcu uruchom:

```text
BUILD_FINAL_REVIEW_ZIP.bat
```

Wygenerowaną paczkę REVIEW warto przed oddaniem sprawdzić po `RESET_REVIEW.bat` / na czystych wolumenach.


## v6.0.2 BUILD hotfix
Poprawiono BUILD_FINAL_REVIEW_ZIP.ps1: katalog projektu jest teraz wyznaczany jako $PSScriptRoot, dzięki czemu review/metadata/snapshot.json jest odczytywany z właściwego katalogu projektu.
