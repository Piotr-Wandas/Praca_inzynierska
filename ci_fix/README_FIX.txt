Financial Prediction v6.3.2 - CI / Ruff Fix

Paczka usuwa problemy widoczne w logu GitHub Actions:
I001, F401, F841, E702, B905, UP017, UP035 przez Ruff --fix/--unsafe-fixes
oraz konfiguruje dwa wyjątki:
E501 - długie linie (m.in. SQL i teksty API; Ruff formatter nie gwarantuje ich łamania)
B008 - wzorzec Query(...) używany przez FastAPI.

INSTALACJA
1. Rozpakuj folder ci_fix do katalogu głównego repozytorium tak, aby było:
   repo/ci_fix/apply_ruff_config_fix.py
   repo/ci_fix/APPLY_CI_FIX.bat

2. Uruchom:
   ci_fix\APPLY_CI_FIX.bat

3. Po komunikacie [OK]:
   git status
   git add .
   git commit -m "Fix CI lint errors"
   git push

WAŻNE
Poprawka dotyczy wszystkich błędów Ruff pokazanych w przekazanym logu.
Jeżeli GitHub Actions po przejściu lintingu ujawni błąd w późniejszym kroku
(np. pytest lub build), będzie to osobny etap CI, którego przekazany log
jeszcze nie pokazywał.
