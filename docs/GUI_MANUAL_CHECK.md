# Obsidian Royale — ręczne sprawdzenie Etapu 2

## Uruchomienie

W PowerShell, z katalogu repozytorium:

```powershell
.\venv\Scripts\python.exe app/gui_app.py
```

Zależności Qt są już zainstalowane w lokalnym `venv`. W nowym środowisku zainstaluj `requirements-gui.txt`; do testów dodatkowo `requirements-dev.txt`, a do TUI dotychczasowy `requirements.txt`.

Normalny start korzysta z istniejącej `data/roulette.db`. Utworzone ręcznie profile pozostają w tej bazie. Automatyczne testy i obrazy kontrolne używały wyłącznie danych tymczasowych. Podczas sprawdzenia zamknij drugą instancję aplikacji grającą tym samym profilem.

## Ekran profili

1. Sprawdź ciemne tło, złote nagłówki i przyciski oraz wyraźne obramowanie aktywnej kontrolki. Okno domyślnie ma 900 × 650; można je powiększać i zmniejszać do 740 × 560.
2. Lista istniejących profili pokazuje nazwę i zapisane saldo. Przy pustej bazie pojawia się komunikat, a fokus trafia do pola nowej nazwy.
3. Wpisz nową nazwę i wybierz **Utwórz profil** lub naciśnij **Enter** w polu nazwy. Oczekiwane: menu gracza i saldo z istniejącego repozytorium (nowy profil domyślnie 1000$).
4. W menu wybierz **Zmień profil**, wpisz tę samą nazwę i spróbuj utworzyć profil ponownie. Oczekiwane: czytelny komunikat o duplikacie, brak drugiego wpisu, zachowana nazwa i fokus w polu.
5. Spróbuj pustej nazwy albo samych spacji. Oczekiwane: komunikat bez utworzenia gracza. Pole pozwala wpisać maksymalnie 40 znaków; białe znaki na końcach są usuwane tak jak w TUI.
6. Zaznacz istniejącego gracza i wybierz **Wybierz profil**. Alternatywnie przejdź na listę klawiszem **Tab**, wybierz strzałkami i zatwierdź **Enter**.
7. **Odśwież listę** ponownie odczytuje repozytorium. Po udanym ponowieniu odczytu stary komunikat błędu znika. Wpisywana nazwa nie znika podczas samego odświeżania.

## Menu i klawiatura

1. Sprawdź nazwę aktywnego gracza i saldo. Przełącz się na inny profil i sprawdź, czy obie wartości się zmieniły.
2. Przejdź do wyboru profilu, a następnie wybierz **Powrót do menu** albo naciśnij **Esc**. Oczekiwane: menu tego samego gracza, bez tworzenia nowej sesji.
3. Użyj **Tab** i **Shift+Tab** do przejścia po dostępnych kontrolkach. Przycisk można zatwierdzić **Spacją** lub **Enter**; pola nazwy i lista mają własną obsługę Enter.
4. Po zmianie rozmiaru sprawdź czytelność. W menu przy małej wysokości lub długiej nazwie dostępne jest przewijanie, aby przycisk wyjścia pozostał osiągalny.
5. Pozycje **Gra**, **Sklep**, **Statystyki**, **Ranking** i **Ustawienia** są obecnie nieaktywne, z informacją po najechaniu. Nie otwierają stołu ani innych funkcji kolejnych etapów.
6. Zamknij aplikację przyciskiem **Wyjdź** i, po ponownym uruchomieniu, systemowym przyciskiem zamknięcia. Profile powinny pozostać dostępne po starcie.

## Blokady i zakres weryfikacji

Podczas odczytu, tworzenia lub otwierania profilu niedozwolone akcje są chwilowo wyłączone. Zamykanie podczas operacji jest odrzucane z komunikatem; po jej zakończeniu można ponowić zamknięcie.

Zmiana profilu, jego utworzenie i zamknięcie są blokowane również przy aktywnych zakładach lub niezapisanej rundzie. Powrót do menu jest blokowany przy niezapisanej rundzie lub animacji; same aktywne zakłady nie gubią sesji przy powrocie, tak jak w TUI. Ponieważ w Etapie 2 nie ma jeszcze ekranu obstawiania, te stany sprawdzają testy integracyjne z istniejącym `GameSession`, bez dodawania przycisków diagnostycznych do aplikacji.

Wykonane przez agentów testy Qt pracowały offscreen, z symulowanymi zdarzeniami myszy i klawiatury. Obejrzano rendery ekranów na danych przykładowych. Nie zastępuje to ręcznego sprawdzenia natywnego okna Windows, skalowania systemowego ani całej rozgrywki.

## Testy automatyczne

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Testy przełączają ścieżkę SQLite na pliki tymczasowe; nie korzystają z roboczej bazy graczy.
