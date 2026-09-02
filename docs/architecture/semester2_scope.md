# Zakres demonstracyjny II semestru

Przepływ demonstracyjny: pobranie -> RAW -> walidacja -> PostgreSQL -> cechy -> point-in-time dataset -> baseline/model -> metryki/MLflow -> predykcja -> FastAPI -> Next.js.

Najważniejsza reguła: żadna cecha nie może mieć `available_at` późniejszego niż `cutoff_at` danej obserwacji.
