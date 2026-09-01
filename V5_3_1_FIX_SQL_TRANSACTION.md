# v5.3.1 – FIX SQL transaction / AmbiguousParameter

Naprawiono błąd `psycopg.errors.AmbiguousParameter` podczas zapisu `core.concept_mapping` oraz wtórny `InFailedSqlTransaction`.

Zmiany:
- osobny SELECT sprawdzający istnienie mapowania,
- INSERT ... VALUES zamiast INSERT ... SELECT,
- jawne CAST-y PostgreSQL dla parametrów tekstowych i confidence,
- SAVEPOINT (`begin_nested()`) wokół pomocniczego zapisu mapowania.

Po aktualizacji przebuduj `api` i `web`, uruchom `init_database.py`, a następnie ponów ingest.
