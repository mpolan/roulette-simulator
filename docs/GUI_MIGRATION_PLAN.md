# Obsidian Royale — plan migracji TUI → GUI

Data audytu: 2026-11-15. Etapy 0–2 ukończone i zaakceptowane; aktualna jednostka pracy: **wyłącznie Etap 3**. Etap 4 wymaga kolejnej akceptacji.

## 1. Stan wejściowy i granice

- Repozytorium: `roulette-simulator`, lokalnie `C:\Pulpit\STUDIA\KCK\Ruletka`.
- Zastana gałąź: `codex`, śledząca `origin/dev`. Nie zmieniano upstreamu ani innych gałęzi.
- Początkowy HEAD i lokalny `main`: `4ba0069f25eb652917a039f76c634fdd1d8d4072` (`Roulette MVP 3.0`). Drzewo robocze i indeks były czyste.
- `app/domain/`, `app/services/`, `app/persistence/` są zamrożone. TUI pozostaje oddzielną, działającą docelowo aplikacją. Etap 0 nie zmienia kodu ani zależności i nie uruchamia gry.
- Stan wejściowy Etapu 0: Python 3.10.6, Textual 8.2.8, Rich 15.0.0; PySide6 i pytest nie były zainstalowane w `venv`, repozytorium nie zawierało zestawu testów. Zależności i testy dodano dopiero w Etapie 1, opisanym w sekcji 5.
- Istnieją lokalne pliki `BUILD.md`, `build.ps1`, `ObsidianRoyale.spec`, `requirements-build.txt` oraz katalogi `build/`, `dist/`, ignorowane przez Git. Nie są częścią audytowanego commita źródeł ani dowodem na aktualność EXE. Nie zmieniano ich.

## 2. Mapa obecnej architektury i zależności

| Obszar | Moduły | Znaczenie dla GUI |
| --- | --- | --- |
| Start TUI | `app/app.py`, `app/ui.py` | `init_db()`, budowa repozytoriów i usług, `RouletteApp.run()`; zachować bez zmian |
| Ekrany TUI | `app/screens/navigation.py`, `game.py`, `statistics.py`, `leaderboard.py`, `shop.py` | Profil, menu, sterowanie grą i blokady; odtworzyć zachowanie w nowej prezentacji |
| Widgety TUI | `app/widgets/roulette_table.py`, `roulette_wheel.py`, `chip_picker.py`, `bet_cart.py`, `badge_label.py` | Zależności Textual i Rich, zdarzenia i renderowanie; nie importować do GUI |
| Styl TUI | `app/ui.tcss` | Nie jest arkuszem Qt; nowy motyw GUI będzie osobny |
| Domena | `app/domain/` | `Game`, `Bet`, `BetType`, `Wheel`, `Pocket`, `RoundResult` oraz modele danych |
| Usługi | `app/services/` | Sesja, fabryka, resolver, walidator, statystyki, ranking, sklep i katalog odznak |
| Persystencja | `app/persistence/` | SQLite, repozytoria profili, rund, zakładów i zakupów |
| Dane demonstracyjne | `app/seed_demo.py` | Narzędzie poza interfejsem; nie uruchamiać na danych użytkownika |

Audyt importów: zamrożone katalogi nie importują Textual ani Rich. Zależności terminalowe pozostają w `ui.py`, `screens/`, `widgets/`; `app.py` zależy od nich pośrednio. Silnik jest już oddzielony od terminala.

Uwaga o importach: obecne moduły używają `domain.*`, `services.*`, `persistence.*`. Uruchomienie `python app/app.py` dodaje `app/` do ścieżki importów. Nie zmieniać importów silnika na `app.domain.*`: grozi to podwójnym ładowaniem klas i problemami z tożsamością `BetType`. Planowany `python app/gui_app.py` ma zachować ten sam układ importów.

## 3. Publiczne API do wykorzystania

| Funkcja GUI | Istniejący kontrakt | Zasady integracji |
| --- | --- | --- |
| Lista i utworzenie profilu | `PlayerRepository.get_all_players()`, `get_player(id)`, `add_player(name)` | Odtworzyć strip/pustą nazwę/limit 40 znaków z TUI, obsłużyć unikalność SQLite; saldo domyślne pochodzi z bazy |
| Wybór profilu | `create_game_session(player_id)` → `GameSession` | Jedna aktywna sesja; przy zakładach/pending blokować przełączenie tak jak TUI |
| Saldo i koszyk | `session.game.player.balance`, `current_bets`, `total_stake`, `chip_stacks` | Silnik jest źródłem stanu; nie odejmować stawki drugi raz w GUI |
| CLASSIC | `Game.place_bet(Bet(...))`, `place_bets(list[Bet])` | Wielokrotny wybór STRAIGHT to osobny zakład z pełną podaną kwotą na każdą liczbę; pakiet przechodzi wspólną walidację i debit |
| CHIPS | `Game.place_chip(kind, value, selection)`, `remove_chip(kind, selection)` | Czytać `CHIP_VALUES` i `MAX_CHIPS_PER_FIELD`, korzystać z limitu silnika oraz usuwania LIFO |
| Usunięcie pozycji | `Game.remove_bet(bet)` | Przekazać ten sam obiekt `Bet`, nie odtworzoną kopię; identyczne pozycje są niezależne |
| Nowa runda | `GameSession.spin_and_save()` → `RoundResult` | Jeden spin i zapis przed animacją; GUI nie wywołuje bezpośrednio `Game.spin()` |
| Ponowienie zapisu | `has_pending_round`, `save_pending_round()` → `RoundResult` | Pozostawić tę samą sesję, blokować mutacje, animować dopiero po udanym zapisie; nie czytać prywatnego `_pending_result` |
| Geometria koła | `Game.wheel.pockets`, `RoundResult.pocket` | 37 pól, kolejność i kolory z silnika; animacja nie losuje |
| Statystyki | `StatsService(RoundRepository()).get_player_stats(id)` | Wyświetlać `PlayerStats`, nie wyliczać ponownie w widoku |
| Ranking | `LeaderboardService(...).get_leaderboard(sort_by)` | Kryteria z `SORT_FIELDS`; zachować filtrację i kolejność serwisu |
| Sklep i kolekcja | `ShopService.get_catalog()`, `get_owned_badges(id)`, `get_total_spent(id)`, `buy_badge(session, badge_id)` | Zakup tylko usługą; ona aktualizuje saldo sesji na podstawie atomowego zakupu |

Obsługiwane zakłady to STRAIGHT, RED, BLACK, EVEN, ODD, LOW, HIGH, DOZEN i COLUMN. STRAIGHT obejmuje 0–36, DOZEN/COLUMN wybór 1–3. Nie dodawać split/street/corner/six-line. CHIPS domyślny, nominały 5/10/25/50/100 i maksymalnie 5 żetonów na pole pochodzą z API. Limit dotyczy stosu CHIPS, nie wszystkich pozycji CLASSIC.

`RoundResult` zawiera `pocket`, indywidualne `bet_results`, `total_stake`, `total_payout`, `net_profit`. Wypłata obejmuje zwrócone stawki zwycięskich zakładów; zysk netto jest osobną wartością. Grupowanie wyniku nie może zmieniać rozliczenia ani obiektów źródłowych.

Ranking: `net_profit`, `total_rounds`, `win_rate`, `badge_count`. Serwis pomija profile bez rund poza sortowaniem odznak; ranking win rate wymaga co najmniej 10 rund, ranking odznak pomija puste kolekcje. Remisy rozstrzyga `player_id`. Win rate oznacza procent rund z dodatnim zyskiem netto; bet win rate jest oddzielną statystyką.

## 4. SQLite i trwałość sesji

- Baza w źródłach: `data/roulette.db` względem katalogu repozytorium, niezależnie od cwd. W EXE: `data/roulette.db` obok pliku wykonywalnego. Zachować `init_db()` oraz istniejące tabele `players`, `rounds`, `round_bets`, `player_badges`.
- `RoundRepository.save_round()` zapisuje rundę, zakłady i saldo w jednej transakcji. `ShopRepository.purchase_badge()` używa transakcji `BEGIN IMMEDIATE` i atomowo sprawdza stan, zapisuje zakup i saldo.
- `spin_and_save()` najpierw rozlicza silnik i opróżnia koszyk, potem zapisuje. Przy błędzie wynik i saldo zostają jako pending w pamięci sesji. `GameSession` blokuje kolejny spin, ale samo `Game` nie blokuje dodawania/usuwania zakładów w pending. Ta blokada należy do kontrolera GUI, tak jak obecnie do TUI.
- Pending nie jest odzyskiwany po zakończeniu procesu. GUI musi blokować normalne zamknięcie/przełączenie profilu do udanego retry; odporność na zabicie procesu nie jest nową funkcją tej migracji.
- Repozytorium nie ma trwałego klucza idempotencji rundy. Test retry ma obejmować jednoznaczną awarię przed zatwierdzeniem transakcji; nie obiecujemy gwarancji pojedynczego zapisu przy niejednoznacznej awarii już po rzeczywistym commit SQLite.
- GUI i TUI nie powinny jednocześnie prowadzić gry tym samym profilem: sesje przechowują saldo w pamięci, a zapis rundy ustawia je w bazie. Zgodność bazy nie oznacza synchronizacji dwóch aktywnych procesów. Nie zmieniać tego kontraktu w ramach migracji.
- Testy integracyjne użyją tymczasowej bazy i podmiany `persistence.database.DB_PATH` w fixture, bez zmian źródeł repozytoriów. Nie kopiować danych prywatnych do repozytorium.

## 5. Docelowa architektura prezentacji — ustalona w Etapie 1

```text
app/gui_app.py                 niezależny start Qt i init_db
app/gui/application.py         QApplication, budowa istniejących zależności
app/gui/main_window.py         trwałe okno i nawigacja QStackedWidget
app/gui/controllers/           obsługa intencji, sesji, blokad, błędów i sygnałów
    application_controller.py  wybór profilu, nawigacja, zamknięcie
    game_controller.py         Game API, spin/save/retry i cykl animacji
app/gui/views/                 profile, menu, gra, statystyki, ranking, sklep
app/gui/widgets/               stół, żetony, koszyk, koło, prezentacja odznak
app/gui/theme.py               wspólna paleta i style Qt
tests/                        regresje silnika oraz testy prezentacji
requirements-gui.txt           zależności GUI, bez usuwania Textual
requirements-dev.txt           zależności testów
pytest.ini                    ścieżki importów i katalog testów
```

To docelowa mapa odpowiedzialności. W Etapie 1 utworzono `app/gui_app.py`, `app/gui/__init__.py`, `app/gui/application.py`, pliki zależności, konfigurację pytest i testy. Etap 2 dodaje `main_window.py`, `controllers/application_controller.py`, `views/profiles.py`, `views/menu.py` i `theme.py`. Pozostałe moduły powstają dopiero w przypisanych im etapach; nie tworzymy pustych katalogów ani zastępczych kontrolerów.

Nie dodawać abstrakcyjnego ORM, event busa ani drugiego modelu domenowego. Sygnały kontrolera przekazują aktualny stan lub niewielkie zmiany do trwałych widgetów. Zmiana żetonu zaznacza selektor; postawienie żetonu aktualizuje dane pola, saldo, koszyk i przycisk SPIN; zakup aktualizuje saldo i odpowiednią kartę/kolekcję.

Punkt startowy `gui_app.py` wywołuje `gui.application.run()`. `create_application(argv)` tworzy lub zwraca istniejący QApplication i stosuje wspólny motyw. Od Etapu 2 `create_main_window()` zastępuje przejściowe `create_bootstrap_window()` właściwym MainWindow. `run()` inicjalizuje istniejącą bazę przez `init_db()`, pokazuje okno, wywołuje `window.start()` i uruchamia pętlę Qt. Sam import niczego nie zapisuje i nie tworzy wątku. Błąd inicjalizacji SQLite lub systemu plików pokazuje polski komunikat i kończy start kodem 1.

MainWindow przechowuje trwały QStackedWidget z trzema widokami: profile, menu i gra (gra dodana w Etapie 3; w Etapie 2 były dwa widoki). ApplicationController obsługuje intencje i blokady; jego worker QObject w pojedynczym QThread wywołuje wyłącznie PlayerRepository oraz istniejącą fabrykę create_game_session. GUI nie tworzy alternatywnego modelu profilu, nie zapisuje własnym SQL i nie ustala salda początkowego. Walidacja pola nazwy odpowiada prezentacji TUI: strip, niepusta nazwa, maksymalnie 40 znaków. Unikalność zapewnia dotychczasowe repozytorium/SQLite. Sesja jest podmieniana dopiero po udanym otwarciu; błąd zachowuje starą sesję. Udane utworzenie profilu i późniejszy błąd otwarcia skutkuje odświeżeniem listy, a nie ponownym tworzeniem tego samego gracza.

Etap 3 dodaje GameController i GameView oraz BettingTable, ChipPicker i BetCart. Kontroler przekłada intencje na publiczne Game.place_chip/remove_chip/place_bets/remove_bet; nie waliduje ponownie reguł gry. Stan formularza CLASSIC i nominał są stanem prezentacji. Każda intencja sprawdza pending oraz centralną navigation_blocked() (busy/animacja/zamykanie). Nawigacja menu–gra zachowuje kontroler, widgety i sesję. Stół ma 49 trwałych QGraphicsObject: 37 liczb oraz 12 pól zewnętrznych i grup; kolory liczb pochodzą z wheel.pockets. Porównanie snapshotów aktualizuje tylko zmienione pola. Koszyk przechowuje osobny QListWidgetItem z referencją do każdego Bet i dodaje/usuwa wyłącznie zmienione wiersze. Sumy na polach są tylko prezentacją. Widok dopasowuje scenę do dostępnego miejsca; koszyk przewija własne pozycje. SPIN jest stale nieaktywny w Etapie 3: brak losowania, rozliczania i zapisu rund z GUI. Pełne sterowanie i zrzuty opisuje GUI_MANUAL_CHECK.md. Cykl spin/save/retry i koło pozostają zakresem Etapu 4.

Motyw Qt zachowuje paletę TUI: #080D14, #121D27, #F5D58C, #A58B58 i #F0EDE5. Widoki mają wspólne panele, przyciski, stany focus/hover/disabled, a nazwy użytkowników są zwykłym tekstem. Dostępne są mysz, Tab/Shift+Tab, Enter/Spacja i Esc przy powrocie. Funkcje późniejszych etapów pozostają widoczne jako nieaktywne pozycje menu. Instrukcja ręcznego sprawdzenia: `GUI_MANUAL_CHECK.md`.

Stół i koło mogą używać QGraphicsScene/QGraphicsView z trwałymi elementami. Animacja: Qt timer lub QPropertyAnimation/QVariantAnimation, stopniowe zwalnianie i zatrzymanie na `RoundResult.pocket`. Stan prezentacji: gotowy → zapis/rozliczenie → animacja → gotowy, z osobnym stanem oczekiwania na ponowienie zapisu. Zakłady i mutacje sesji blokowane przy pending/animacji; profil dodatkowo przy aktywnych zakładach. Po ręcznym sprawdzeniu Etapu 3 użytkownik zlecił wyjątek dla zamykania GUI: aktywne zakłady można anulować po potwierdzeniu i zamknąć aplikację. MainWindow pokazuje jeden nieblokujący QMessageBox.open(); domyślny przycisk, Esc i zamknięcie dialogu wracają do gry. X, Alt+F4, Ctrl+Q i Wyjdź używają tego samego closeEvent. ApplicationController.shutdown(cancel_bets=True) ponownie sprawdza pending/busy/animację/zamykanie, następnie usuwa każdy oryginalny Bet przez Game.remove_bet() i uruchamia dotychczasowe wygaszanie workera. Bez zakładów nie ma dialogu; pending nadal blokuje wyjście i wymaga ponowienia zapisu. Powrót z gry do menu jest blokowany przy pending/animacji, a przy samych zakładach zachowuje tę samą sesję, zgodnie z TUI. Przechwytujemy także spóźnione/podwójne sygnały. Wspólne kontrolery edytuje jeden wykonawca naraz. Ta korekta dotyczy tylko zamykania GUI i nie zmienia TUI ani zasad gry.

SQLite może czekać na blokadę dysku. Od Etapu 2 odczyt listy oraz tworzenie i otwieranie profilu odbywają się w pojedynczym workerze QObject/QThread, z żądaniami i wynikami przez sygnały Qt. Kontroler dopuszcza jedną operację naraz. Worker nie dotyka widgetów. Repozytoria tworzą połączenia wewnątrz operacji, więc połączeń SQLite nie przenosimy między wątkami. Podczas operacji zamknięcie jest odrzucane z komunikatem; po jej zakończeniu można je ponowić. Przy zwykłym zamykaniu okno pozostaje żywe do pełnego zakończenia wątku. Po `finished` sprawdza to nieblokujące `wait(0)` i w razie potrzeby timer ponawiający; dopiero wtedy wysyłane jest `shutdown_finished`. Wynika to z [kontraktu QThread](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html), w którym samo finished może poprzedzać końcowe sprzątanie natywnego wątku. Nie ma blokującego wait, sleep ani terminate w GUI. Jednorazowy `init_db()` pozostaje przed pokazaniem okna. Aktualizacje widgetów zawsze w wątku Qt.

Zależności są rozdzielone: dotychczasowy `requirements.txt` pozostaje bez zmian, `requirements-gui.txt` dodaje `PySide6==6.12.0`, a `requirements-dev.txt` dodaje `pytest==8.4.2`. Wersje dobrano dla Python 3.10.6 / Windows x64 i zweryfikowano w indeksie pip oraz w metadanych [PySide6](https://pypi.org/project/PySide6/6.12.0/) i [pytest](https://pypi.org/project/pytest/8.4.2/). Bootstrap korzysta z oficjalnego modelu [Qt Widgets: QApplication, QWidget i pętla exec](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/widgets.html). Testy nie wymagają pytest-qt ani pytest-asyncio; Qt pracuje offscreen, a smoke Textual używa `asyncio.run()` i `run_test()`.

## 6. Ryzyka i wymagania regresyjne

| Ryzyko | Wymagana kontrola w kolejnych etapach |
| --- | --- |
| Podwójny debit/wypłata/losowanie | Deterministyczne wyniki koła, licznik wywołań spin, salda i wyniki wszystkich BetType, zero oraz granice grup |
| Odrzucenie pakietu pozostawia część zakładów | Niepoprawny zakład i niewystarczające saldo: brak zmian koszyka i salda |
| Identyczne zakłady usuwane razem | Tożsamość `Bet`, zwrot jednej stawki, synchronizacja stosów, odrzucenie nieaktywnej kopii |
| Błędny limit CHIPS | Nominały, 5/6 żeton, LIFO, niezależne pola i mieszanie CLASSIC/CHIPS |
| Błąd zapisu i reroll | Wymuszona awaria repozytorium, pending, blokada kolejnego spin, retry tego samego wyniku, jedna runda po sukcesie |
| Częściowy zapis rundy lub zakupu | Rollback transakcji, nieistniejący profil, duplikat odznaki, brak środków |
| Utrata sesji przy nawigacji | Blokada profilu przy zakładach/pending/animacji; zamknięcie z zakładami tylko po potwierdzeniu anulowania, pending/animacja blokują wyjście; powrót do menu nie tworzy nowej sesji |
| Błędne statystyki/ranking | Puste konto, zysk 0, payout ze zwrotem stawki, wszystkie 4 sortowania, progi 9/10 rund, remisy, kolekcja odznak |
| Zależność GUI od TUI | Start GUI bez importowania `ui`, `screens`, `widgets` TUI; TUI uruchamialne bez PySide6 |
| Animacja pokazuje inny wynik lub blokuje UI | Każde z 37 pól, anulowanie timerów przy zamknięciu, brak dodatkowego RNG, responsywność i blokady do sygnału końca |
| Regresja TUI lub formatu bazy | Test TUI na tymczasowej bazie oraz odczyt schematu/funkcji istniejących repozytoriów; kontrola diffu zamrożonych katalogów |
| Utrata danych przy wydaniu | Osobny artefakt GUI EXE, zachowanie TUI, brak nadpisania `data/roulette.db` |

Etap 1 tworzy i uruchamia testy bazowe na obecnym silniku, bez modyfikacji zamrożonych źródeł. Etapy funkcjonalne dodają testy integracji swoich widoków/kontrolerów. Audyt statyczny Etapu 0 nie zastępuje tych testów.

## 7. Konfiguracja i role Codexa

Zweryfikowano lokalne `codex-cli 0.169.0`, katalog `codex debug models`, dostępne narzędzie delegacji oraz oficjalne [definicje subagentów](https://learn.chatgpt.com/docs/agent-configuration/subagents) i [referencję konfiguracji](https://learn.chatgpt.com/docs/config-file/config-reference). Wszystkie poniższe identyfikatory i poziomy reasoning występują w katalogu środowiska; nie stosowano zamienników. W Etapie 0 faktycznie uruchomiono audytora i QA, co nie stanowi testu wykonania każdego pozostałego modelu.

Konfiguracja `.codex/config.toml` ustawia koordynatora `gpt-6.1-sol` / `high`, `agents.enabled = true` i `agents.max_concurrent_threads_per_session = 2`. Każdy `.codex/agents/<nazwa>.toml` zawiera `name`, `description`, `model`, `model_reasoning_effort`, `developer_instructions`. Stosujemy aktualny format samodzielnych agentów; nie dokładamy starej flagi eksperymentalnej ani nie zmieniamy globalnych uprawnień.

| Rola | Model | Reasoning | Zakres zapisu po akceptacji odpowiedniego etapu |
| --- | --- | --- | --- |
| architecture_auditor | gpt-6-astra | medium | Brak, audyt do odczytu |
| project_setup | gpt-6.1-terra | low | `app/gui_app.py`, `app/gui/__init__.py`, `app/gui/application.py`, `requirements-gui.txt`, `requirements-dev.txt`, `pytest.ini`, `tests/conftest.py` |
| gui_shell | gpt-6.1-terra | medium | `app/gui/main_window.py`, `controllers/application_controller.py`, `views/profiles.py`, `views/menu.py`, `tests/gui/test_profiles.py` |
| betting_table | gpt-6.1-sol | high | `app/gui/controllers/game_controller.py`, `views/game.py`, `widgets/betting_table.py`, `chip_picker.py`, `bet_cart.py`, `tests/gui/test_betting.py` |
| wheel_animator | gpt-6-astra | medium | `app/gui/widgets/roulette_wheel.py`, `controllers/game_controller.py`, `views/game.py`, `tests/gui/test_wheel.py` |
| statistics_gui | gpt-6.1-terra | high | `app/gui/views/statistics.py`, `widgets/badge_collection.py`, `tests/gui/test_statistics.py` |
| leaderboard_gui | gpt-6.1-terra | high | `app/gui/views/leaderboard.py`, `tests/gui/test_leaderboard.py` |
| shop_gui | gpt-6.1-terra | high | `app/gui/views/shop.py`, `widgets/badge_card.py`, `tests/gui/test_shop.py` |
| ux_optimizer | gpt-6.1-sol | high | `app/gui/theme.py`, `main_window.py`, `views/`, `widgets/`, `tests/gui/test_accessibility.py` — tylko prezentacja |
| qa_reviewer | gpt-6-astra | medium | Brak, niezależna ocena i uruchamianie uzgodnionych kontroli |
| docs_writer | gpt-6-luna | low | `README.md`, `docs/GUI_USER_GUIDE.md`, `docs/GUI_RELEASE.md`; propozycje do dziennika przekazuje koordynatorowi |

Skrócone ścieżki w tabeli są rozwinięte jednoznacznie w plikach TOML. Koordynator odpowiada za plan, dziennik, testy regresyjne Etapu 1, integrację wspólnych plików i Git. Audytor ani QA nie mogą samodzielnie rozszerzać zakresu. Limity zapisu w instrukcjach nie są izolacją OS.

W sesji Etapu 0 narzędzie delegacji przyjmowało nazwę zadania, jawny model i reasoning, bez parametru wyboru projektowej roli. Role audytowe uruchomiono wówczas jawnie z tymi ustawieniami i zakazem edycji. Nie deklarowano przeładowania nowych TOML w działającej sesji. Zalecono ponowne sprawdzenie przy wznowieniu; późniejszą skuteczną weryfikację natywną opisano poniżej.

Weryfikacja CLI ma ograniczenie: `--strict-config app-server --print-startup-config` kończy się poprawnie, ale `config/read` z cwd projektu pokazał, że osobne konto procesu sandboxa nie ufa temu projektowi i pomija jego warstwę. Jednorazowa flaga trust w CLI nie zmieniła tej sytuacji. To nie jest dowód aktywacji konfiguracji projektu. Potwierdzono składnię 12 TOML i zgodność pól z dokumentacją; efektywnego zastosowania ustawień w nowym czacie trzeba dopilnować przy wznowieniu. Nie zmieniano plików zaufania ani konfiguracji globalnej.

**Aktualizacja bramki przed Etapem 1:** powyższe dwa akapity opisują stan z Etapu 0. Natywne narzędzie bieżącej sesji udostępnia już `agent_type` i wszystkie 11 nazwanych ról z przypisanymi modelami/effort. Rola `architecture_auditor` została faktycznie uruchomiona i zakończyła audyt do odczytu; definicja narzędzia przypisuje jej niezmienne `gpt-6-astra / medium`. Limit sesji to 3 sloty łącznie z koordynatorem, czyli 2 subagentów. Zgodnie z późniejszą instrukcją użytkownika jest to wystarczające potwierdzenie do rozpoczęcia Etapu 1. Nie wnioskujemy o aktywnym modelu koordynatora z samego pliku TOML i nie diagnozujemy dalej zaufania poprzez osobny CLI. Nie zmieniono uprawnień ani konfiguracji bezpieczeństwa.

## 8. Etapy i kryteria odbioru

| Etap | Wykonawca | Zakres i warunek zakończenia |
| --- | --- | --- |
| 0 — Bootstrap i audyt | Koordynator + architecture_auditor + qa_reviewer | Audyt API/TUI/ryzyk, AGENTS, 11 ról, konfiguracja, plan i dziennik; bez GUI i zmian silnika; commit i stop |
| 1 — Testy bazowe i architektura | project_setup + koordynator; przegląd audytora/QA | Regresje, struktura GUI, niezależny start, zależności Qt zgodne z Pythonem, TUI smoke na izolowanej bazie |
| 2 — Okno i profile | gui_shell | Nawigacja, tworzenie/wybór profili, menu, istniejąca sesja/repozytoria, blokady |
| 3 — Stół i obstawianie | betting_table | Wszystkie obecne BetType, CHIPS/CLASSIC, koszyk, saldo, stosy/usuwanie/limity/błędy, testy zgodności Game |
| 4 — Koło i animacja | wheel_animator | Kolejność i kolory 37 pól z silnika, płynny obrót do RoundResult, spin/save/retry, blokady i testy |
| 5 — Statystyki | statistics_gui | StatsService i kolekcja odznak, puste stany i testy prezentacji |
| 6 — Leaderboard | leaderboard_gui | Wszystkie sortowania serwisu, oznaczenie aktywnego profilu, progi i remisy |
| 7 — Prestige Shop | shop_gui | Karty odznak, ShopService, saldo i kolekcja, błędy zakupu i blokady |
| 8 — UX i wydajność | ux_optimizer | Rozmiary, klawiatura, hover/focus, spójność i dostępność, aktualizacje częściowe, pomiary responsywności/animacji |
| 9 — Testy i wydanie | qa_reviewer + project_setup + docs_writer | Regresje końcowe, zgodność TUI/GUI, audyt katalogów, instrukcja, świeży EXE Windows GUI i zachowane dane |

Po każdym etapie: kontrola diffu, testy adekwatne do zmian, aktualizacja `GUI_PROGRESS.md`, logiczny Conventional Commit na `codex`, raport z SHA i stop. Bez merge/rebase/push. Następny etap rozpoczyna dopiero dokładna akceptacja użytkownika.
