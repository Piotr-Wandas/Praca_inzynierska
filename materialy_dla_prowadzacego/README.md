# Materiały do sprawdzenia pracy inżynierskiej

Zacznij od `03_dokumentacja/RAPORT_PRZEGLADU.md`. Przegląd wskazuje zgodność opisu z kodem i ograniczenia wymagające poprawy przed finalnymi eksperymentami.

## Baza danych

W folderze `01_baza_danych` znajdują się kompletne skrypty SQL. Na istniejącej, pustej bazie PostgreSQL 16 uruchom kolejno:

```bash
psql -v ON_ERROR_STOP=1 -U fp_app -d financial_platform -f materialy_dla_prowadzacego/01_baza_danych/01_create_database.sql
psql -v ON_ERROR_STOP=1 -U fp_app -d financial_platform -f materialy_dla_prowadzacego/01_baza_danych/02_analytics_views.sql
```

Po załadowaniu danych uruchom `04_kontrole_do_pracy.sql`. Skrypt tworzący schemat nie pobiera i nie uzupełnia danych. Skopiowano też oryginalne kontrole jakości; ich zapytanie porównujące fakty z predykcjami jest szeroką diagnostyką, a nie dowodem użycia późniejszej informacji przez model.

Nie uruchamiaj zamiennie początkowej migracji Alembic i tego DDL na tej samej bazie. Starsze `db/models.py` nie odwzorowuje obecnego schematu SQL. Główna ścieżka aplikacji korzysta z SQL.

## Kod analizy

Pełne kopie ważnych modułów znajdują się w `02_analiza_danych/kod_zrodlowy`. Oryginały w `src/financial_platform` pozostają źródłem kodu aplikacji. Kopie służą do czytania; zgodność sprawdza:

```bash
python materialy_dla_prowadzacego/sprawdz_kopie.py
```

Do uruchamiania aplikacji użyj Pythona 3.11 lub 3.12 i zależności z `pyproject.toml`. Dla samodzielnej analizy CSV wystarczą pandas i numpy; przeliczenie metryk wykorzystuje też scikit-learn.

Wszystkie poniższe polecenia wykonuj z katalogu głównego repozytorium. Katalog wynikowy musi być nowy.

```bash
python materialy_dla_prowadzacego/02_analiza_danych/analiza_panelu.py --input data/demo/panel_demo.csv --output wyniki_demo --data-kind demo
python materialy_dla_prowadzacego/02_analiza_danych/analiza_zapisanych_wynikow.py --output wyniki_archiwalne
```

Pierwszy skrypt oblicza statystyki opisowe; DEMO nie mierzy jakości prognoz na rzeczywistych spółkach. Drugi przelicza zapisane predykcje z `review/artifacts/real_data_analysis`, porównuje metryki i sprawdza klucze obserwacji oraz daty odcięcia. Nie odtwarza treningu ani nie wczytuje modeli joblib.

Po skonfigurowaniu połączenia z istniejącą bazą zgodnie z README aplikacji:

```bash
python materialy_dla_prowadzacego/02_analiza_danych/eksport_panelu.py --output eksport_panelu
python materialy_dla_prowadzacego/02_analiza_danych/analiza_panelu.py --input eksport_panelu/panel.csv --output wyniki_panelu --data-kind real
```

Eksport używa obecnego buildera. Nie naprawia i nie potwierdza historycznej poprawności panelu. Wartości muszą zostać zweryfikowane z raportami emitentów.

## Prezentacja

W przekazanym `review/metadata/snapshot.json` ustawiono `prepared=false`; plik danych SQL jest pusty poza komentarzami. Zapisane CSV i modele nie zastępują kompletnej bazy REVIEW. Aby prowadzący mógł uruchomić prezentację z danymi, przygotuj snapshot na komputerze z uzupełnioną bazą, zgodnie z instrukcją REVIEW. Miejsca na rysunki i listingi opisano w poprawionym opracowaniu oraz w `03_dokumentacja/ILUSTRACJE_I_LISTINGI.md`.
