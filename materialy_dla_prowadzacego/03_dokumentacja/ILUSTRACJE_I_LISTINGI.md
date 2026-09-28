# Ilustracje i listingi

[MIEJSCE NA RYSUNEK 1]
Ekran główny systemu
Komentarz do wstawienia: Wstawić pełny zrzut strony głównej po uruchomieniu aplikacji. Na obrazie powinny być widoczne: nazwa systemu, krótki opis rozwiązania, pasek nawigacyjny oraz informacja o statusie backendu lub danych. Nie przycinać menu.

[MIEJSCE NA RYSUNEK 2]
Podgląd danych rynkowych
Komentarz do wstawienia: W zakładce „Podgląd danych” wybrać zbiór „Notowania dzienne”, ustawić jedną spółkę i zakres około 20–30 sesji. Na zrzucie powinny być widoczne kolumny: ticker, data sesji, open, high, low, close, volume oraz możliwość sortowania.

[MIEJSCE NA RYSUNEK 3]
Podgląd danych fundamentalnych
W zakładce „Podgląd danych” wybrać jedną spółkę i pojęcie zysku netto. Pokazać okres, wartość, jednostkę i dostępne daty. Jeśli interfejs nie wyświetla revision_no, is_current lub source_label, wykonać dodatkowy odczyt w pgAdmin i wstawić go jako osobny panel tego rysunku.

Listing 1. Konfiguracja mapowania spółek na identyfikatory źródeł

Listing 2. Rejestr cech i ich zakres zastosowania

[MIEJSCE NA RYSUNEK 4]
Dashboard jakości danych
Komentarz do wstawienia: Wstawić górną część zakładki „Dane”: karty z liczbą wierszy panelu, liczbą spółek, okresów i pokryciem targetu oraz wykres pokrycia w czasie. Filtry powinny być ustawione na pełny dataset.

[MIEJSCE NA RYSUNEK 5]
Kompletność cech z podziałem sektorowym
Komentarz do wstawienia: W tej samej zakładce przewinąć do sekcji kompletności cech. Na zrzucie muszą być widoczne procenty pokrycia oraz etykiety zakresu: cały panel, banki, spółki niefinansowe.

Listing 3. Tworzenie logicznych schematów bazy

Listing 4. Najważniejsze pola faktu finansowego

[MIEJSCE NA RYSUNEK 6]
Diagram ERD bazy danych
Komentarz do wstawienia: Wstawić diagram ERD wygenerowany z PostgreSQL/pgAdmin lub narzędzia modelującego. Diagram powinien obejmować co najmniej: company, sector, daily_price, financial_concept, financial_fact, macro_series, macro_observation, training_run, prediction i feature_importance. Należy zadbać o czytelność kluczy PK/FK.

Listing 5. Kontrola chronologicznej dostępności cech

Listing 6. Łączenie point-in-time typu as-of

[MIEJSCE NA RYSUNEK 7]
Panel modelowy i daty odcięcia
W „Podglądzie danych” wybrać dataset modelowy i jedną spółkę. Pokazać period_end, cutoff_at, target_period_end, net_income_lag1, net_income_lag4 i target_net_income. Pod rysunkiem wyjaśnić różnicę między datą okresu a datą dostępności; nie podpisywać bieżącego panelu jako w pełni zweryfikowanego point-in-time.

Listing 7. Fabryka modeli i preprocessing

Listing 8. Walidacja walk-forward

[MIEJSCE NA RYSUNEK 8]
Schemat walidacji walk-forward
Komentarz do wstawienia: Wstawić własny diagram osi czasu. Pokazać co najmniej 4 foldy: rosnący niebieski blok TRAIN oraz kolejny pojedynczy czerwony/żółty okres TEST. Diagram nie powinien pochodzić ze screena aplikacji, tylko być prostą grafiką metodologiczną.

Listing 9. Implementacja zestawu metryk regresji

[MIEJSCE NA RYSUNEK 9]
Feature Importance dla wybranego modelu
Komentarz do wstawienia: W zakładce „Analizy” ustawić target net_income i wybrać model ML z dostępnym permutation importance. Wstawić wykres poziomych słupków z 8–12 najważniejszymi cechami, z pełnymi nazwami osi.

[MIEJSCE NA RYSUNEK 10]
Architektura logiczna platformy
Wstawić własny diagram: Yahoo Finance, Bankier i NBP → pobieranie danych → PostgreSQL → budowa panelu i trening → zapis wyników → FastAPI → Next.js. GUS, MLflow, Prefect i DVC oznaczyć jako elementy częściowo przygotowane lub demonstracyjne, bez sugerowania pełnej integracji głównego procesu.

Listing 10. Fragment definicji usług kontenerowych

Listing 11. Przykładowe endpointy FastAPI w projekcie

[MIEJSCE NA RYSUNEK 11]
Dokumentacja Swagger API
Komentarz do wstawienia: Otworzyć http://localhost:8000/docs. Wstawić zrzut pokazujący listę endpointów /api/v1, w tym analytics, data-browser, dashboard oraz admin/train. Nie trzeba rozwijać wszystkich odpowiedzi.

[MIEJSCE NA RYSUNEK 12]
Interaktywna przeglądarka danych
Komentarz do wstawienia: Wstawić screenshot zakładki „Podgląd danych” z widocznymi filtrami, sortowaniem po kolumnie i paginacją. Najlepiej użyć datasetu modelowego i ustawić jedną spółkę, aby wartości były czytelne.

[MIEJSCE NA RYSUNEK 13]
Górna część interaktywnego dashboardu
Komentarz do wstawienia: W zakładce „Analizy” ustawić target net_income, wybrać model i pełny zakres dat. Zrzut powinien obejmować filtry oraz karty MAE, RMSE, sMAPE, R², liczbę obserwacji OOF i liczbę spółek.

[MIEJSCE NA RYSUNEK 14]
Actual vs Predicted
Komentarz do wstawienia: W zakładce „Analizy” ustawić jedną spółkę z kilkoma predykcjami OOF. Wstawić wykres rzeczywistego wyniku i predykcji w czasie oraz, jeśli mieści się na ekranie, scatter Actual vs Predicted.

[MIEJSCE NA RYSUNEK 15]
Porównanie modeli i błędy per spółka
Komentarz do wstawienia: Wstawić dolną część zakładki „Analizy” z rankingiem modeli oraz tabelą/wykresem MAE według spółek. Upewnić się, że widoczna jest liczba obserwacji, aby nie porównywać wyników bez kontekstu.

[MIEJSCE NA RYSUNEK 16]
Ekran REVIEW
Komentarz do wstawienia: Po przygotowaniu finalnego snapshotu uruchomić START_REVIEW.bat i wstawić screenshot strony /review. Na obrazie powinny być widoczne: wersja snapshotu/datasetu, liczba danych, status treningów oraz linki do kolejnych ekranów.

[MIEJSCE NA LISTING 12]
Po naprawie wersjonowania wstawić 10–20 linii faktycznego zapytania odtwarzającego wersję financial_fact dostępną przy cutoff. Podać ścieżkę pliku i funkcję. Fragment ma pochodzić z poprawionej, sprawdzonej implementacji.

[MIEJSCE NA LISTING 13]
Po dodaniu kontroli dostępności etykiet wstawić fragment podziału treningowego wykorzystującego target_available_at oraz odpowiadający mu test.