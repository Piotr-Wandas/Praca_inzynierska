# Financial Prediction — v6.0.1 REVIEW RELEASE

## Dla prowadzącego

1. Zainstaluj i uruchom Docker Desktop.
2. Rozpakuj całą paczkę do zwykłego katalogu na dysku.
3. Uruchom **START_REVIEW.bat**.
4. Po pozytywnej kontroli system automatycznie otworzy stronę **http://localhost:3000/review**.

Przy pierwszym uruchomieniu Docker może potrzebować kilku minut na zbudowanie/pobranie obrazów. Nie jest wymagane pobieranie danych finansowych z internetu ani ponowne trenowanie modeli — paczka FINAL REVIEW zawiera zamrożony snapshot bazy oraz zapisane wyniki eksperymentów.

### Najważniejsze ekrany

- `/review` — stan wersji badawczej i informacje o snapshotcie,
- `/data` — jakość i przygotowanie danych,
- `/data-browser` — filtrowanie, sortowanie i podgląd rekordów,
- `/models` — porównanie modeli,
- `/dashboard` — zbiorczy dashboard analityczny,
- `http://localhost:8000/docs` — dokumentacja REST API.

## Dla autora pracy

Przed przekazaniem paczki prowadzącemu należy na komputerze z kompletną bazą wykonać **PREPARE_REVIEW_SNAPSHOT.bat**, a następnie **BUILD_FINAL_REVIEW_ZIP.bat**. To zamraża aktualny stan danych i wyników modeli. Dopiero wygenerowany plik `Financial_Prediction_v6_0_REVIEW_READY.zip` jest paczką przeznaczoną do oddania.

Nie przekazuj `.env` ani kluczy API. Snapshot REVIEW ma umożliwiać ocenę bez dostępu do prywatnych sekretów i bez zależności od bieżącej dostępności zewnętrznych serwisów.


## v6.0.2 BUILD hotfix
Poprawiono BUILD_FINAL_REVIEW_ZIP.ps1: katalog projektu jest teraz wyznaczany jako $PSScriptRoot, dzięki czemu review/metadata/snapshot.json jest odczytywany z właściwego katalogu projektu.
