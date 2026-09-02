# v6.0.1 REVIEW RELEASE

Wersja przygotowana do reprodukowalnej prezentacji pracy. Tryb REVIEW uruchamia system z zamrożonym snapshotem PostgreSQL oraz zapisanymi artefaktami modeli. Dzięki temu prowadzący nie musi podczas oceny wykonywać ETL z internetu ani czekać na trening.

## Przepływ autora

1. Uruchomić pełne pobieranie i trening na zweryfikowanej bazie.
2. `PREPARE_REVIEW_SNAPSHOT.bat` — eksport bazy i artefaktów.
3. `BUILD_FINAL_REVIEW_ZIP.bat` — budowa finalnej paczki.
4. Przetestować finalną paczkę: `RESET_REVIEW.bat`, potem `START_REVIEW.bat`.

## Przepływ prowadzącego

Tylko `START_REVIEW.bat`.

## Reprodukowalność

Snapshot zawiera dane znajdujące się w PostgreSQL oraz rekordy `ml.training_run` i `ml.prediction`. Metadane snapshotu znajdują się w `review/metadata/snapshot.json`. Wersja REVIEW nie wymaga kluczy API.
