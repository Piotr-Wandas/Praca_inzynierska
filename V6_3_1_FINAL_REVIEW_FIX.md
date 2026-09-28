# v6.3.1 FINAL REVIEW FIX

Poprawka dotyczy procesu przygotowania paczki dla prowadzacego.

## Naprawione problemy
- START_REVIEW nie sprawdza juz JSON przez FINDSTR; snapshot jest parsowany przez PowerShell/ConvertFrom-Json.
- BUILD_FINAL_REVIEW_ZIP waliduje snapshot, dump PostgreSQL i pliki uruchomieniowe przed spakowaniem.
- Gotowy ZIP jest automatycznie rozpakowywany do katalogu tymczasowego i ponownie walidowany.
- ZIP nie zostanie uznany za gotowy, jezeli brakuje snapshot.json lub dumpu bazy.
- Nazewnictwo paczki zostalo ujednolicone do v6.3.1.
- START_REVIEW uruchamia REVIEW na czystych wolumenach projektu, aby PostgreSQL odtworzyl dump przy pierwszym starcie.

## Kolejnosc dla autora
1. Uruchom i uzupelnij normalny projekt.
2. PREPARE_REVIEW_SNAPSHOT.bat
3. BUILD_FINAL_REVIEW_ZIP.bat
4. Rozpakuj Financial_Prediction_v6_3_1_FINAL_REVIEW.zip do nowego katalogu.
5. Uruchom START_REVIEW.bat z rozpakowanej paczki.

## Dla prowadzacego
Po rozpakowaniu FINAL_REVIEW wystarczy Docker Desktop i START_REVIEW.bat.
