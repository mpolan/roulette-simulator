# Obsidian Royale — ręczne sprawdzenie Etapu 3

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
5. **Gra** otwiera stół obstawiania. **Sklep**, **Statystyki**, **Ranking** i **Ustawienia** pozostają nieaktywne, z informacją po najechaniu.
6. Zamknij aplikację przyciskiem **Wyjdź** i, po ponownym uruchomieniu, systemowym przyciskiem zamknięcia. Profile powinny pozostać dostępne po starcie.

## Blokady i zakres weryfikacji

Podczas odczytu, tworzenia lub otwierania profilu niedozwolone akcje są chwilowo wyłączone. Zamykanie podczas operacji jest odrzucane z komunikatem; po jej zakończeniu można ponowić zamknięcie.

Zmiana profilu i jego utworzenie pozostają blokowane przy aktywnych zakładach lub niezapisanej rundzie. Zamknięcie przy aktywnych zakładach wymaga potwierdzenia ich anulowania; niezapisana runda nadal blokuje wyjście. Powrót do menu jest blokowany przy niezapisanej rundzie lub animacji; same aktywne zakłady nie gubią sesji przy powrocie, tak jak w TUI. Pending i animację sprawdzają testy integracyjne z istniejącym `GameSession`, bez dodawania przycisków diagnostycznych do aplikacji.

## Zamykanie aplikacji — poprawka po ręcznym sprawdzeniu Etapu 3

1. Bez zakładów zamknij aplikację przez systemowy **X**, **Alt+F4**, **Ctrl+Q** albo **Wyjdź**. Oczekiwane: zwykłe zamknięcie bez potwierdzenia, po zakończeniu workera Qt.
2. Postaw żeton i dodaj identyczny zakład CLASSIC. Użyj X lub skrótu zamykania. Dialog oferuje **Anuluj zakłady i zamknij** oraz **Wróć do gry**. Samo pokazanie dialogu nie zmienia salda ani koszyka; okno nie przyjmuje innych interakcji do podjęcia decyzji.
3. Wybierz **Wróć do gry**, naciśnij **Esc** albo zamknij sam dialog. **Enter** na domyślnym przycisku także wraca do gry. Oczekiwane: ta sama sesja, wszystkie zakłady i saldo bez zmian, widoczny stół.
4. Ponów zamknięcie i wybierz **Anuluj zakłady i zamknij**. Oczekiwane: każda oryginalna pozycja jest usunięta przez `Game.remove_bet()`, wszystkie stawki zwrócone w sesji, stosy puste, aplikacja zamknięta. Nie następuje losowanie ani zapis rundy. Anulowanie nie wymaga aktualizacji bazy, ponieważ samo obstawianie nie zapisywało salda w SQLite.
5. Przy `has_pending_round` nie ma opcji anulowania ani zamknięcia: pasek stanu informuje **Najpierw ponów zapis oczekującej rundy**. Busy i animacja także zachowują dotychczasowe blokady. Stan pending sprawdzają testy; GUI Etapu 3 nadal nie udostępnia spin/retry.

## Stół i CHIPS

1. Z menu wybierz **Gra**. Oczekiwane: liczby 0–36, zielone zero, czerwone/czarne pola zgodne z kołem silnika, trzy kolumny, trzy tuziny i sześć zakładów zewnętrznych. Kolumny odpowiadają rzędom liczb: 1/4/…/34, 2/5/…/35, 3/6/…/36.
2. Domyślny tryb to **CHIPS**, nominał **25**. Wybierz kolejno żetony **5, 10, 25, 50, 100**. Zaznaczenie powinno być czytelne i zmieniać wyłącznie selektor.
3. Kliknij lewym przyciskiem pole 0, liczbę czerwoną, czarną oraz pola zewnętrzne. Każde kliknięcie dodaje jeden żeton, pokazuje go na danym polu i dopisuje jedną pozycję koszyka. Saldo maleje o nominał, łączna stawka rośnie o tę samą kwotę.
4. Na jednym polu postaw kolejno 5, 10 i 25. Prawy przycisk usuwa ostatni żeton (**25**) i zwraca dokładnie jego stawkę. Następne usunięcie zwraca 10. Puste pole zgłasza błąd bez zmiany salda.
5. Dodaj pięć żetonów do jednego pola, a potem spróbuj szóstego. Oczekiwane: komunikat o limicie; stos, saldo i koszyk pozostają bez zmian. Na innym polu nadal można postawić żeton, jeśli wystarcza salda.
6. Przy niewystarczającym saldzie próba dodania żetonu kończy się komunikatem i nie zmienia zaakceptowanych zakładów.

## CLASSIC i wszystkie typy zakładów

1. Przełącz tryb na **CLASSIC**. Dotychczasowe zakłady i stosy pozostają w sesji. Zmiana trybu nie nalicza ani nie zwraca stawki.
2. Wybierz **STRAIGHT**, zaznacz na stole 0, 1 i 36, wpisz 10 i zatwierdź zakład. Oczekiwane: trzy osobne pozycje po 10, koszt całego pakietu 30. Ponowne kliknięcie zaznaczonej liczby przed zatwierdzeniem ją odznacza.
3. Sprawdź **RED, BLACK, EVEN, ODD, LOW (1–18), HIGH (19–36)**, następnie **DOZEN** i **COLUMN** dla każdej grupy 1, 2, 3. Wyboru można dokonać formularzem albo klikając odpowiednie pole stołu. Każde zatwierdzenie tworzy zakład przez istniejące API Game.
4. Wprowadź pustą stawkę, tekst, zero i liczbę ujemną. Oczekiwane: błąd bez zmiany salda lub koszyka. Zaznacz kilka liczb i podaj stawkę, dla której łączny koszt przekracza saldo: odrzucony jest cały pakiet, bez częściowego dodania.
5. Zatwierdź dwa identyczne zakłady CLASSIC. Usuń tylko jeden z koszyka: drugi pozostaje, a zwrot obejmuje jedną stawkę. Limit pięciu dotyczy wyłącznie stosu CHIPS; CLASSIC może zawierać więcej identycznych pozycji.

## Koszyk, nawigacja i klawiatura

1. Zaznacz pozycję koszyka i wybierz usunięcie lub wykonaj dwuklik. **Delete/Backspace** usuwa zaznaczoną pozycję. Usunięcie pozycji CHIPS aktualizuje również właściwy stos na stole.
2. Na stole używaj **strzałek** do zmiany aktywnego pola, **Enter/Spacji** do dodania żetonu lub wyboru pola CLASSIC, **Delete/Backspace** do usunięcia ostatniego żetonu CHIPS. Aktywne pole ma widoczne oznaczenie fokusu.
3. **Alt+1…5** wybiera nominały w kolejności 5/10/25/50/100, **Alt+C** przełącza CHIPS/CLASSIC. **Tab/Shift+Tab** przechodzi między kontrolkami; **Enter/Spacja** uruchamia przyciski, **Enter** w stawce lub **Ctrl+Enter** w widoku gry zatwierdza CLASSIC.
4. Naciśnij **Esc** albo **Powrót do menu** z aktywnymi zakładami. W menu saldo odpowiada sesji, zmiana profilu jest zablokowana, a **Wyjdź** otwiera potwierdzenie anulowania zakładów. Ponowne wejście w **Gra** pokazuje te same zakłady, tryb i nominał.
5. Usuń wszystkie zakłady. Saldo wraca do wartości sprzed obstawiania, a zmiana profilu i zamknięcie stają się dostępne. Samo obstawianie nie zapisuje rund w SQLite.
6. Sprawdź okno przy **900 × 650**, **1280 × 800** i **740 × 560**. Stół dopasowuje skalę do miejsca, a koszyk przewija własne pozycje. Cały widok gry nie ma przewijania. Wszystkie pola mają pozostać osiągalne; etykiety liczb i nominały nie powinny się zlewać.
7. **SPIN pozostaje nieaktywny w Etapie 3**, również z zakładami. Nie uruchamia RNG, zapisu ani rozliczenia. Koło, animacja i spin/save/retry należą do Etapu 4.

Zestaw pytest pracuje offscreen, z symulowanymi zdarzeniami myszy i klawiatury. Dodatkowy smoke koordynatora użył natywnego backendu Qt **windows**, rzeczywistych widgetów i zdarzeń QTest: 12 kolejnych cykli otwarcia okna, wyboru profilu, obstawiania/usuwania, menu i zamknięcia; po poprawce geometrii żetonów powtórzono 12 cykli. Wszystkie dane były tymczasowe. Historyczna natywna awaria Etapu 2 nie powtórzyła się. Nie dowodzi to usunięcia jej pierwotnej przyczyny i nie zastępuje sprawdzenia różnych ustawień Windows/DPI ani całej rozgrywki.

## Zrzuty kontrolne

Zrzuty wykonano przez QWidget.grab() z natywnego backendu Qt Windows, na profilu demonstracyjnym w tymczasowej bazie, po poprawce geometrii żetonów. Nie zawierają danych użytkownika.

- [CHIPS 900 × 650](images/gui-stage3-chips-900x650.png)
- [CHIPS 1280 × 800](images/gui-stage3-chips-1280x800.png)
- [CHIPS 740 × 560](images/gui-stage3-chips-740x560.png)
- [CLASSIC 900 × 650](images/gui-stage3-classic-900x650.png)

## Testy automatyczne

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Testy przełączają ścieżkę SQLite na pliki tymczasowe; nie korzystają z roboczej bazy graczy.
