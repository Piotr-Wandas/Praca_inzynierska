# Przegląd repozytorium i opracowania pracy inżynierskiej

Przegląd rozpoczęto 9 września i zakończono 11 września 2026 r. Obejmuje przekazaną paczkę źródłową, opracowanie teoretyczne, instrukcję realizacji i pakiet na II semestr. Obecna aplikacja jest prototypem. Opis wymagał korekty szczególnie w zakresie point-in-time, wersjonowania, reguł bazowych i odtwarzalności prezentacji.

## Zakres zmian

Opracowanie uporządkowano według dziesięciu rozdziałów ze wskazanego planu. Rozbudowano cel, problem badawczy, opis relacji w bazie, metodykę i część wynikową. Zachowano i doprecyzowano 16 miejsc na ilustracje oraz 11 listingów, dodając dwa miejsca na fragmenty przyszłej poprawionej implementacji. Przeredagowano stwierdzenia sugerujące gotowe funkcje, których główna ścieżka jeszcze nie realizuje. Dodano prawdziwe archiwalne wyniki CSV wraz z ograniczeniami interpretacji.

W repozytorium dodano ten folder, pełne kopie SQL i 13 modułów analitycznych, eksport panelu, analizę opisową CSV, przeliczenie archiwalnych metryk oraz odtwarzalne kontrprzykłady. Zmieniono wstęp README_START_HERE.md. Logika aplikacji i modeli w `src` nie była zmieniana. Raport wskazuje usterki do dalszej naprawy; nie należy traktować tej paczki jako ich usunięcia.

## Ustalenia i zalecane poprawki

| Priorytet | Obszar i dowód w repozytorium | Ustalenie oraz znaczenie |
| --- | --- | --- |
| Wysoki | `services/model_dataset.py`, `_financial_panel` | Odczytuje `is_current=TRUE`, a następnie wybiera najnowszy fakt po `available_at`. Nie odtwarza wersji fundamentalnej dla historycznego cutoff. |
| Wysoki | `services/internet_ingestion.py`, `_store_financial_fact` | Wstawia `revision_no=1`, a konflikt aktualizuje wartość. Pola historii istnieją, ale nie gwarantują zachowania każdej korekty. Potrzebna niezmienna historia wersji. |
| Wysoki | `services/train_from_db.py`, `_splits` | Podział używa `period_end`; nie sprawdza daty dostępności etykiety. Trening musi odrzucać wyniki nieznane w momencie prognozy. |
| Wysoki | `services/model_dataset.py`, `_add_lags`; `train_from_db.py`, `model_predictions` | Cel jest przesunięty o −1, a baseline używa lag1/lag4 względem wiersza wejściowego. Dla celu t+1 poprawne reguły to t i t−3 przy ciągłości i znanych publikacjach. |
| Wysoki | `services/model_dataset.py`, `shift(-1)` | Następny wiersz nie musi być następnym kwartałem. Kontrprzykład łączy 2019Q2 z 2019Q4 po usunięciu Q3. |
| Wysoki | `review/artifacts/real_data_analysis/*/oof_predictions_common_sample.csv` | Wszystkie daty odcięcia przypadają po końcu okresu docelowego. To nie są prognozy przed zakończeniem tego kwartału. Do oceny nowcastingu potrzebna jest data publikacji celu; sama relacja dat nie dowodzi przecieku. |
| Wysoki | `sql/create_database.sql`, `db/models.py`, `migrations/versions/0001_initial.py` | Główny DDL i starszy ORM są różne. Przykłady: `company.sector_id` kontra `sector` i klucz pojęcia finansowego kontra tekst. Nie stosować zamiennie obu inicjalizacji. |
| Wysoki | `review/metadata/snapshot.json`, `review/database/900-review-data.sql` | `prepared=false`, SQL zawiera tylko komentarze. Brak pełnego snapshotu do uruchomienia prezentacji z danymi. CSV i joblib są dostępne, lecz nie zastępują bazy. |
| Wysoki | `services/internet_ingestion.py`, `ingest_bankier_fundamentals` | Bieżące fakty są dezaktywowane przed próbą pobrania nowych. Przy obsłużonym błędzie źródła mogą pozostać nieaktywne. Nowe dane należy najpierw pobrać i zweryfikować, a przełączenie wykonać po sukcesie. |
| Średni | `config/universe.py` | Lista PILOT_COMPANIES ma 13 spółek. Nie jest historycznym składem WIG20. Tabela index_membership nie steruje głównym pobieraniem/panelem. |
| Średni | `ingestion/bankier_financials.py`, `ingestion/yahoo_finance.py` | Zastępcza dostępność +120 dni jest przybliżeniem. Oznaczanie proxy jest przydatne, lecz nie stanowi dowodu rzeczywistych publikacji. |
| Średni | `ingestion/gus_bdl.py`, `services/internet_ingestion.py` | GUS ma osobny adapter z przybliżeniem dostępności na czas pobrania. Główna ścieżka wykorzystuje trzy kursy NBP, nie pełny zestaw wskaźników GUS. |
| Średni | `datasets/point_in_time.py`, `asof_latest` | Sortowanie po spółce, a potem czasie może naruszyć globalne uporządkowanie wymagane przez merge_asof. Odtworzono wyjątek `left keys must be sorted`. Główny builder łączy rynek per spółka, więc wymaga odrębnej oceny. |
| Średni | `datasets/point_in_time.py`, `assert_point_in_time` | Kontrola obejmuje tylko nazwy z końcówką `_available_at`. Brak takich kolumn albo historycznych wersji nie jest automatycznie wykrywany. |
| Średni | `services/train_from_db.py`, `permutation_importance` | Ważność liczona jest na treningu końcowym (8 powtórzeń, negMAE). Nie opisuje potwierdzonego wpływu poza próbą. Nie ma SHAP w głównej ścieżce. |
| Średni | `services/train_from_db.py`, `_create_training_context` | Wersja zbioru otrzymuje kod czasowy, ale nie wszystkie pola pochodzenia, Git i sum kontrolnych są uzupełnione. Odtwarzalność wymaga utrwalenia wejścia, konfiguracji i wersji kodu. |
| Średni | `flows/demo_training_flow.py`, `dvc.yaml` | Prefect i DVC obejmują demonstrację; główny trening zapisuje SQL/joblib bez wywołań MLflow. Nie opisywać tego jako pełnej orkiestracji produkcyjnej. |
| Średni | API i moduły danych/analityki | Panel jest budowany i stronicowany w pandas, podczas gdy pozostałe zbiory korzystają z SQL. Tabela porównania modeli i ważność cech nie są przeliczane według wszystkich filtrów ekranu. |
| Średni | API analiz | Dla wielu spółek szereg jest sumą wartości. Lista obserwacji ma limit 250; karty metryk obejmują wybrany zbiór. Interpretacja musi wskazywać zakres agregacji. |
| Przed udostępnieniem publicznym | `apps/api/app/main.py`, operacje admin | Operacje pobierania i treningu nie wymagają uwierzytelnienia. Do prezentacji lokalnej ograniczyć dostęp; przed publicznym wdrożeniem dodać autoryzację. |

Ścieżki skrócone `services`, `datasets`, `db`, `modeling` i `config` odnoszą się do `src/financial_platform`.

## Przeprowadzona weryfikacja

| Kontrola | Wynik | Ograniczenie |
| --- | --- | --- |
| Istniejący zestaw pytest | 20 passed | Nie obejmuje pełnego środowiska Docker/PostgreSQL/przeglądarki. |
| Ruff | 254 zgłoszenia | Głównie 193 E501 i 22 I001; nie naprawiano hurtowo kodu. |
| Parser SQL | Akceptacja 4 plików, odpowiednio 45/4/4/7 instrukcji | Nie wykonano skryptów na serwerze PostgreSQL. |
| Kopie kodu i SQL | 16 zgodnych par | Po zmianach oryginałów należy odświeżyć kopie i manifest. |
| Analiza opisowa DEMO | 64 wiersze, 4 spółki, brak duplikatów klucza | To dane syntetyczne, nie wynik badania rzeczywistych prognoz. |
| Kontrprzykład baseline | Cel 106; kod last 104 zamiast 105, seasonal 101 zamiast 102 | Sztuczny przykład pokazujący wyrównanie. |
| Kontrprzykład dostępności | 16 późniejszych etykiet trafia do treningu pierwszego badanego foldu | Dowód braku warunku w funkcji; nie pomiar rozmiaru przecieku w historycznym zbiorze. |
| Archiwalne CSV | 6 metryk × 5 modeli × 3 cele zgodne z plikami podsumowania | Nie odtwarza treningu ani nie sprawdza raportów źródłowych. |

Logi, wersje bibliotek i JSON znajdują się w `04_weryfikacja`. Skrypt reprodukcji drukuje wyniki i nie zmienia bazy. Nie uruchomiono pełnego pobierania danych, migracji na serwerze ani testów interfejsu.

## Archiwalne wyniki

Każdy cel ma 25 foldów, z okresami docelowymi 2020-06-30–2026-06-30. Modele w obrębie celu mają identyczne klucze obserwacji i brak duplikatów na model.

| Cel | Obserwacje na model | Spółki | Najniższe zapisane MAE |
| --- | ---: | --- | --- |
| Zysk netto | 124 | CDR, DNP, ORL, PEO, PKO | Random Forest: ok. 858,14 mln PLN |
| Przychody | 74 | CDR, DNP, ORL | Random Forest: ok. 3837,08 mln PLN |
| Wynik odsetkowy | 50 | PEO, PKO | baseline_last_value: ok. 446,94 mln PLN |

Jednostki przeliczono z wartości zapisanych przez aplikację, bez niezależnego potwierdzenia raportów emitentów. Dla przychodów baseline_last_value ma niższe RMSE i sMAPE niż Random Forest. Nie należy wybierać zwycięzcy bez wskazania metryki ani przedstawiać tych różnic jako dowodu poprawnej prognozy ex ante.

## Zgodność z planem i dalsze kroki

Wymaganie II semestru obejmuje wstępną treść całej pracy i wstępne rozwiązanie praktyczne. Poprawiona treść ma kompletną strukturę, ale finalne badanie wymaga dalszych prac. Plan techniczny nie jest potwierdzeniem wykonania wszystkich wymienionych funkcji.

1. Uzgodnić finalny zakres: lista pilotażowa czy historyczny WIG20; prognoza przed końcem kwartału czy nowcasting przed publikacją.
2. Poprawić wersjonowanie faktów, daty dostępności etykiet, ciągłość okresów i wyrównanie baseline. Ujednolicić schemat i migracje oraz dodać testy tych konkretnych zachowań.
3. Przygotować kompletny eksport bazy i sprawdzić próbkę wartości, jednostek oraz publikacji w raportach źródłowych.
4. Wykonać kontrolowane eksperymenty, utrwalić wejście i wersję kodu oraz uzupełnić rozdział wynikowy. Nie zastępować brakujących rezultatów danymi demonstracyjnymi.
5. Uruchomić REVIEW, wykonać wskazane zrzuty i diagramy oraz uaktualnić spis treści i podpisy w Wordzie.

Nie zmieniono logiki modeli bez nowego zbioru i walidacji. Wprowadzenie takich zmian zmieniłoby interpretację już zapisanych artefaktów i wymagałoby ponownego treningu.
