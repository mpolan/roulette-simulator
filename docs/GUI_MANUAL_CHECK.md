# Obsidian Royale — ręczne sprawdzenie Etapu 7

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
5. **Gra** otwiera stół obstawiania, a **Statystyki** — statystyki i kolekcję aktywnego profilu. **Ranking** otwiera leaderboard. **Prestige Shop** otwiera sklep odznak. **Ustawienia** pozostają nieaktywne.
6. Zamknij aplikację przyciskiem **Wyjdź** i, po ponownym uruchomieniu, systemowym przyciskiem zamknięcia. Profile powinny pozostać dostępne po starcie.

## Blokady i zakres weryfikacji

Podczas odczytu, tworzenia lub otwierania profilu niedozwolone akcje są chwilowo wyłączone. Zamykanie podczas operacji jest odrzucane z komunikatem; po jej zakończeniu można ponowić zamknięcie.

Zmiana profilu i jego utworzenie pozostają blokowane przy aktywnych zakładach lub niezapisanej rundzie. Zamknięcie przy aktywnych zakładach wymaga potwierdzenia ich anulowania; niezapisana runda nadal blokuje wyjście. Powrót do menu jest blokowany przy niezapisanej rundzie lub animacji; same aktywne zakłady nie gubią sesji przy powrocie, tak jak w TUI. Pending i animację sprawdzają testy integracyjne z istniejącym `GameSession`, bez dodawania przycisków diagnostycznych do aplikacji.

## Zamykanie aplikacji — poprawka po ręcznym sprawdzeniu Etapu 3

1. Bez zakładów zamknij aplikację przez systemowy **X**, **Alt+F4**, **Ctrl+Q** albo **Wyjdź**. Oczekiwane: zwykłe zamknięcie bez potwierdzenia, po zakończeniu workera Qt.
2. Postaw żeton i dodaj identyczny zakład CLASSIC. Użyj X lub skrótu zamykania. Dialog oferuje **Anuluj zakłady i zamknij** oraz **Wróć do gry**. Samo pokazanie dialogu nie zmienia salda ani koszyka; okno nie przyjmuje innych interakcji do podjęcia decyzji.
3. Wybierz **Wróć do gry**, naciśnij **Esc** albo zamknij sam dialog. **Enter** na domyślnym przycisku także wraca do gry. Oczekiwane: ta sama sesja, wszystkie zakłady i saldo bez zmian, widoczny stół.
4. Ponów zamknięcie i wybierz **Anuluj zakłady i zamknij**. Oczekiwane: każda oryginalna pozycja jest usunięta przez `Game.remove_bet()`, wszystkie stawki zwrócone w sesji, stosy puste, aplikacja zamknięta. Nie następuje losowanie ani zapis rundy. Anulowanie nie wymaga aktualizacji bazy, ponieważ samo obstawianie nie zapisywało salda w SQLite.
5. Przy `has_pending_round` nie ma opcji anulowania ani zamknięcia: pasek stanu informuje **Najpierw ponów zapis oczekującej rundy**. Użyj **Ponów zapis** w widoku gry. Busy i animacja także zachowują dotychczasowe blokady.

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
7. **SPIN** jest aktywny przy zaakceptowanych zakładach i braku blokad. Pusty koszyk nie pozwala rozpocząć rundy.

## Koło, wynik i kolejna runda

1. Postaw kilka zakładów i naciśnij **SPIN** lub **Ctrl+Spacja**. Operacja rozlicza i zapisuje rundę przez istniejącą sesję, następnie pokazuje obracające się koło. Koło ma 37 pól w kolejności silnika, zielone zero i nieruchomy wskaźnik u góry.
2. Obserwuj płynne zwalnianie. Podczas zapisu i animacji zakłady, kolejny SPIN, nawigacja oraz zamknięcie są zablokowane; okno nadal odświeża się i można zmieniać jego rozmiar.
3. Po zatrzymaniu numer pod wskaźnikiem odpowiada wynikowi w panelu. Sprawdź numer i kolor, wygrane/przegrane pozycje, stawkę, wypłatę oraz bilans netto. **Wypłata obejmuje zwrócone stawki wygranych zakładów**, bilans netto jest osobną wartością z silnika.
4. Wybierz **Obstawiaj dalej**, postaw zakład i rozpocznij następną rundę. **Ostatni wynik** pozwala wrócić do poprzedniego wyniku; powrót do menu i gry zachowuje sesję. Zmiana profilu czyści wynik prezentacji.
5. W razie błędu zapisu użyj **Ponów zapis** lub **Ctrl+R**. Obstawianie i wyjście pozostają zablokowane do udanego zapisu; ponowienie zapisuje ten sam wynik bez nowego losowania. Animacja rozpoczyna się dopiero po powodzeniu zapisu. Celowany test automatyczny wymusza ten błąd na tymczasowej bazie; nie ma przycisku diagnostycznego w aplikacji.
6. Sprawdź koło i wynik przy 900 × 650 oraz 740 × 560. Lista wyników zakładów ma własne przewijanie. Zamykanie z aktywnymi zakładami nadal korzysta z opisanego wyżej potwierdzenia anulowania.

Historyczne kontrole Etapu 3, w tym próby natywnego Qt i ograniczenia diagnozy jego awarii, opisuje `GUI_PROGRESS.md`. W Etapie 4 wykonano tylko celowane testy i jeden natywny smoke na tymczasowej bazie. Nie zastępują one kontroli wszystkich ustawień Windows/DPI ani pełnej regresji zaplanowanej na Etap 9.

## Statystyki i kolekcja odznak

1. W menu wybierz **Statystyki**. Sprawdź nazwę profilu i **zapisane saldo**. Aktywne zakłady nie zmieniają zapisanej historii ani tego salda; powrót do menu i gry zachowuje sesję oraz jej zakłady.
2. Sekcje Rozgrywka, Finanse i Skuteczność pokazują wszystkie wartości z TUI. Odróżnij procent rund z zyskiem od procentu wygranych zakładów oraz wypłatę od bilansu netto. Dodatni/ujemny bilans ma subtelne oznaczenie kolorem.
3. Sprawdź nowy profil bez rund: zera, skuteczność 0.00% i czytelny komunikat. Pusta kolekcja ma własny komunikat. Zakupione odznaki pokazują symbole i nazwy; obok widoczne są liczba odznak i łączna wydana kwota.
4. **Odśwież** ponownie pobiera gotowe dane z usług i repozytorium. **Tab/Shift+Tab** przechodzi między kontrolkami, **Enter/Spacja** uruchamia przyciski, **Esc** wraca do menu. Podczas odczytu akcje są chwilowo zablokowane. Po zmianie profilu nie mogą pozostać dane poprzedniego gracza.
5. Przy błędzie odczytu pojawia się komunikat i możliwość ponownego odświeżenia. Poprzednie dane tego samego profilu pozostają do czasu udanego odczytu; test wymusza błąd na danych tymczasowych.
6. Sprawdź czytelność przy 900 × 650 i 740 × 560; przewijaj zawartość w mniejszym oknie. Po zakupie w Prestige Shop wejdź ponownie w Statystyki i sprawdź kolekcję, wydaną kwotę oraz zapisane saldo.

## Ranking

1. W menu wybierz **Ranking**. Domyślnie jest to Zysk netto. Sprawdź pozycję, nazwę, zysk, rundy, skuteczność rund z zyskiem, liczbę odznak i zapisane saldo. Symbole zakupionych odznak znajdują się przy nazwie; po najechaniu widać ich nazwy. Saldo i statystyki są zapisanymi danymi, niezależnymi od bieżących zakładów sesji.
2. Zmień kryterium kolejno na liczbę rund, skuteczność i liczbę odznak. Kolejność pochodzi z serwisu: minimum jedna runda dla zysku/aktywności, minimum 10 dla skuteczności, minimum jedna kupiona odznaka dla kolekcjonerów. Remisy rozstrzyga identyfikator gracza. Zmiana kryterium aktualizuje ten sam ekran.
3. Aktywny profil ma zielone tło, dopisek **(Ty)** i pozycję nad tabelą. Przy braku kwalifikacji pojawia się odpowiednia wskazówka. Pusty ranking podaje przyczynę i sposób dołączenia. Pierwsze trzy pozycje mają złote, srebrne i brązowe oznaczenia; dodatni/ujemny zysk jest zielony/czerwony.
4. **Odśwież** ponawia odczyt. W razie błędu można spróbować ponownie; poprzedni wynik tego kryterium pozostaje widoczny z komunikatem. Po zmianie kryterium stare wiersze są czyszczone, aby nie przedstawiać ich jako nowego rankingu. Błąd odczytu wymuszają testy na bazie tymczasowej.
5. **Tab/Shift+Tab** przechodzi między kontrolkami. Kryterium wybieraj strzałkami lub z listy, przyciski uruchamiaj **Enter/Spacją**, tabelę przewijaj myszą lub klawiaturą. **Powrót do menu/Esc** zachowuje tę samą sesję. Zmień profil i wejdź ponownie: wyróżnienie i pozycja mają odpowiadać nowemu graczowi.
6. Sprawdź 900×650 i 740×560 oraz przewijanie przy wielu graczach. Przy zapisie, pending lub animacji obowiązują dotychczasowe blokady nawigacji. Zamykanie i anulowanie aktywnych zakładów działają jak wcześniej.

## Prestige Shop

1. W menu wybierz **Prestige Shop**. Sprawdź nazwę aktywnego gracza, dostępne saldo sesji i pięć kart z nazwą, symbolem, opisem oraz ceną z katalogu. Odznaki są wyłącznie kosmetyczne. Przy mniejszym oknie przewijaj karty w dół.
2. Mając wystarczające środki, wybierz **Kup**. Oczekiwane: jeden zakup, komunikat powodzenia, karta **POSIADANA** i saldo zmienione przez usługę. Szybkie powtarzanie kliknięć nie może naliczyć kilku zakupów. Podczas operacji zakup, odświeżanie, nawigacja i zamknięcie są chwilowo zablokowane.
3. Posiadanej odznaki nie można kupić ponownie. Dla zbyt drogiej karty widoczna jest brakująca kwota i nieaktywny przycisk **Brak środków**. Zachowane są identyfikatory i ceny 2500/5000/10000/25000/50000$.
4. Wróć do gry, postaw żeton i otwórz sklep przez menu. Zakupy są zablokowane z wyjaśnieniem, a oglądanie, odświeżanie i powrót do menu pozostają dostępne. Usuń zakłady i ponownie wejdź do sklepu. Pending i animacja nadal blokują zakupy/nawigację; najpierw ponów zapis w grze lub poczekaj na koło.
5. **Odśwież** pobiera katalog i kolekcję. Przy błędzie odczytu lub zakupu komunikat prosi o odświeżenie; do udanego odczytu zakupy pozostają zablokowane. Transakcja nie jest automatycznie ponawiana. Błędy i blokady testy wymuszają na tymczasowej bazie, bez zmiany danych użytkownika.
6. Wybierz **Powrót do menu** lub **Esc**, otwórz **Statystyki**, następnie **Ranking → Kolekcjonerzy**. Zakupiona odznaka i zaktualizowane saldo powinny być widoczne w obu ekranach. Zmień profil i sprawdź, czy sklep pokazuje nowego gracza oraz jego kolekcję.
7. **Tab/Shift+Tab** przechodzi po dostępnych przyciskach, **Enter/Spacja** uruchamia zakup/odświeżenie/powrót, **Esc** wraca do menu. Sprawdź 900×650 i 740×560, w tym dojście klawiaturą do niższych kart. Zamknięcie z aktywnymi zakładami zachowuje dotychczasowy dialog anulowania.

## Zrzuty kontrolne

Etap 7: [Prestige Shop, 900 × 650](images/gui-stage7-shop-900x650.png), natywny backend Qt Windows, demonstracyjny zakup na tymczasowej bazie. Sprawdzono też przewijany układ 740 × 560 oraz odznakę w statystykach i rankingu.


Etap 6: [ranking, 900 × 650](images/gui-stage6-leaderboard-900x650.png), natywny backend Qt Windows, wyłącznie demonstracyjne profile/rundy/zakupy na tymczasowej bazie. Obejrzano także 740 × 560.

Etap 5: [statystyki i odznaki, 900 × 650](images/gui-stage5-statistics-900x650.png), natywny backend Qt Windows, profil demonstracyjny na tymczasowej bazie. Kontrola obejmowała też rozmiar 740 × 560; mniejszy widok ma przewijanie.

Etap 4: [koło i wynik, 900 × 650](images/gui-stage4-result-900x650.png), natywny backend Qt Windows, przykładowa runda na tymczasowej bazie. Jeden smoke nowej rundy, bez serii stabilności i pełnego zestawu testów; awaria Qt nie wystąpiła. Historyczne ograniczenie diagnozy pozostaje w dzienniku.

Zrzuty wykonano przez QWidget.grab() z natywnego backendu Qt Windows, na profilu demonstracyjnym w tymczasowej bazie, po poprawce geometrii żetonów. Nie zawierają danych użytkownika.

- [CHIPS 900 × 650](images/gui-stage3-chips-900x650.png)
- [CHIPS 1280 × 800](images/gui-stage3-chips-1280x800.png)
- [CHIPS 740 × 560](images/gui-stage3-chips-740x560.png)
- [CLASSIC 900 × 650](images/gui-stage3-classic-900x650.png)

## Testy automatyczne

```powershell
.\venv\Scripts\python.exe -X faulthandler -m pytest -q tests/gui/test_shop.py tests/test_import_boundaries.py
```

Testy przełączają ścieżkę SQLite na pliki tymczasowe; nie korzystają z roboczej bazy graczy.
