# Materiały po przeglądzie pracy

Skrypty SQL, kod analizy i raport przeglądu są w [materialy_dla_prowadzacego](materialy_dla_prowadzacego/README.md).
Przed prezentacją uzupełnij snapshot REVIEW — dostarczona wersja nie zawiera gotowego eksportu bazy.

# Financial Prediction — v6.1 INTERACTIVE ANALYTICS REVIEW

## Dla prowadzącego

1. Zainstaluj i uruchom Docker Desktop.
2. Rozpakuj całą paczkę.
3. Uruchom **START_REVIEW.bat**.
4. Po kontroli system automatycznie otworzy **http://localhost:3000/review**.

Snapshot REVIEW zawiera zamrożone dane i wyniki treningów, dlatego podczas oceny nie jest wymagane ponowne pobieranie danych ani trenowanie modeli.

### Najważniejsze ekrany

- `/review` — ścieżka prezentacji i metadane snapshotu,
- `/data` — przygotowanie i jakość danych,
- `/data-browser` — filtrowanie, sortowanie i podgląd konkretnych rekordów,
- `/analytics` — **interaktywny dashboard analityczny** z filtrami target/model/spółka/sektor/okres,
- `/models` — formalne porównanie modeli,
- `/dashboard` — stan pipeline'u i diagnostyka techniczna,
- `http://localhost:8000/docs` — dokumentacja REST API.

## Dla autora pracy

Przed przekazaniem paczki prowadzącemu uruchom na komputerze z kompletną bazą:

1. `PREPARE_REVIEW_SNAPSHOT.bat`
2. `BUILD_FINAL_REVIEW_ZIP.bat`

Finalny plik będzie nosił nazwę `Financial_Prediction_v6_1_INTERACTIVE_ANALYTICS_REVIEW_READY.zip`.

Nie przekazuj `.env` ani kluczy API. Snapshot ma umożliwiać ocenę bez dostępu do prywatnych sekretów i bez zależności od bieżącej dostępności źródeł zewnętrznych.

## Nowości v6.1

Interaktywny dashboard korzysta bezpośrednio z `ml.prediction`, `ml.training_run` i `ml.feature_importance`. Filtry są wykonywane przez FastAPI/PostgreSQL. Przy nowym treningu modeli ML zapisywana jest permutation importance, dzięki czemu ekran interpretowalności nie wymaga danych demonstracyjnych.
