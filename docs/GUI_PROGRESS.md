# Obsidian Royale — dziennik migracji GUI

## Stan i bramka akceptacji

- Aktualizacja: 2026-11-15.
- Aktualnie zaakceptowany ukończony etap: **Etap 0**, przez wiadomość `ZATWIERDZAM ETAP 0 — PRZEJDŹ DO ETAPU 1`.
- Etap 1: **ukończony; oczekiwanie na akceptację wyniku**, po pozytywnym teście natywnej delegacji wymaganym przez użytkownika. Etapy 2–9 nierozpoczęte.
- Etap 0: ukończony i zaakceptowany.
- Gałąź: `codex`; początkowy commit: `4ba0069f25eb652917a039f76c634fdd1d8d4072` (`Roulette MVP 3.0`). Początkowy status czysty, brak wcześniejszych zmian użytkownika.
- Ostatni commit konfiguracji: `7c5bacfcebe0bf0af4fbbcc4d40d39e2a1e9de38` — `chore(gui): configure project agents` (13 plików: AGENTS i konfiguracja ról).
- Ostatni commit poprzedniego etapu: `954cc707e866067446fe8bf1084da673c8a31657` — dokumentacja audytu.
- Ostatni commit implementacji Etapu 1: `69a187fd4395664903697f3ba23a7d13a008a1c3` — `feat(gui): bootstrap Qt and add baseline regressions`.
- Ostatni commit bieżącej dokumentacji: do ustalenia przez `git log -1 --format="%H %s" -- docs/GUI_PROGRESS.md`; SHA zostanie podany w raporcie czatu. Własnego SHA nie wpisujemy do treści tego samego commita.
- Kontynuacja do Etapu 2 wyłącznie po: `ZATWIERDZAM ETAP 1 — PRZEJDŹ DO ETAPU 2`.

| Etap | Stan | Akceptacja |
| --- | --- | --- |
| 0 — Bootstrap i audyt | Ukończony | Udzielona |
| 1 — Testy bazowe i architektura | Ukończony | Oczekiwana po raporcie |
| 2 — Główne okno i profile | Nierozpoczęty | Brak |
| 3 — Stół i obstawianie | Nierozpoczęty | Brak |
| 4 — Koło i animacja | Nierozpoczęty | Brak |
| 5 — Statystyki | Nierozpoczęty | Brak |
| 6 — Leaderboard | Nierozpoczęty | Brak |
| 7 — Prestige Shop | Nierozpoczęty | Brak |
| 8 — UX i wydajność | Nierozpoczęty | Brak |
| 9 — Testy i wydanie | Nierozpoczęty | Brak |

## Ustalenia Etapu 0

1. Zweryfikowano katalog repozytorium, gałąź, HEAD, status, lokalny main i upstream. Nie przełączano gałęzi i nie zmieniano upstreamu `origin/dev`.
2. Audyt publicznych API i zależności Textual znajduje się w `GUI_MIGRATION_PLAN.md`. Zamrożony silnik nie zależy od Textual/Rich; nie znaleziono potrzeby modyfikowania zamrożonych modułów w celu dodania GUI.
3. Przyjęto kierunek PySide6/Qt Widgets i prosty podział widoki–kontrolery–istniejący silnik. Struktura w planie jest propozycją do ostatecznego ustalenia w Etapie 1.
4. Opracowano wymagania regresyjne dotyczące rozliczeń, tożsamości zakładów, CHIPS, pending/retry, transakcji, profili, statystyk, rankingu i sklepu.
5. Przygotowano `AGENTS.md`, `.codex/config.toml` i 11 samodzielnych definicji ról `.codex/agents/*.toml`. Limit projektu: 2 subagentów poza koordynatorem.
6. Sprawdzono oficjalny format konfiguracji i lokalne CLI 0.169.0. `codex debug models` potwierdza wymagane modele i poziomy reasoning; brak zamienników. Nie testowano wykonania wszystkich 11 ról.

## Faktycznie użyci agenci Etapu 0

| Rola | Model | Reasoning | Zadanie |
| --- | --- | --- | --- |
| architecture_auditor | gpt-6-astra | medium | Niezależny audyt API, zależności i ryzyk, bez edycji |
| qa_reviewer | gpt-6-astra | medium | Końcowy przegląd artefaktów Etapu 0, bez edycji |

Koordynator docelowo: `gpt-6.1-sol`, `high`. Role w bieżącej sesji wywoływane przez narzędzie delegacji z jawnym modelem i reasoning; nie przypisujemy ich uruchomienia automatycznemu wczytaniu nowej konfiguracji. Nie przekroczono dwóch aktywnych subagentów.

## Weryfikacja Etapu 0

- OK: parser `pip._vendor.tomli` z obecnego venv odczytał 12 plików TOML; sprawdzono komplet 11 nazw, modele, reasoning, instrukcje i limit 2.
- OK: analiza AST 42 plików Python; 26 plików zamrożonej warstwy bez importów Textual/Rich/PySide6. Nie importowano aplikacji ani repozytoriów do uruchomienia.
- OK: `git diff --exit-code 4ba0069f25eb652917a039f76c634fdd1d8d4072 -- app requirements.txt` potwierdza brak zmian całej aplikacji i zależności; kontrola diffu obejmuje również staged pliki Etapu 0.
- OK: niezależny QA nie znalazł istotnych uwag blokujących commit; potwierdził 12 TOML, mapę API i zakres plików.
- OK: przegląd jawnie dodanych plików w indeksie oraz `git diff --cached --check`; do commitów wchodzą wyłącznie 15 nowych plików konfiguracji i dokumentacji. Bez zmian istniejących źródeł.
- Częściowo: `codex --strict-config app-server --print-startup-config` exit 0. Dodatkowy odczyt `config/read` z cwd wykazał pomijanie warstwy projektu przez brak zaufania w osobnym koncie procesu sandboxa. Jednorazowa flaga trust nie włączyła warstwy (asercja efektywnego modelu nie przeszła). Nie zmieniano globalnego zaufania. Składnia i format są sprawdzone, aktywacja ustawień w nowym czacie pozostaje do potwierdzenia.
- Kontrola roboczej bazy: odczytano wyłącznie rozmiar/hash pliku, bez otwierania SQLite i wywołania `init_db()`. Końcowy hash porównano z kontrolnym odczytem podczas etapu; to kontrola braku zmian podczas prac, nie test kompatybilności danych.

Nie uruchamiano TUI/GUI, testów rozgrywki, baseline regresji ani buildu EXE. Nie ma jeszcze GUI do ręcznego sprawdzenia. Testy bazowe i weryfikacja uruchomienia TUI należą do Etapu 1. Żadne dane użytkownika nie są częścią commita.

## Etap 1 — konfiguracja, architektura i regresje

### Bramka natywnej delegacji

Po początkowym wstrzymaniu użytkownik polecił zweryfikować konfigurację przez natywne narzędzie sesji, bez ponownego dodawania zaufania i bez opierania oceny na osobnym CLI. Narzędzie udostępnia teraz wszystkie 11 nazwanych ról przez `agent_type` oraz limit 3 slotów z koordynatorem (2 subagentów).

Uruchomiono `architecture_auditor` jako zadanie `architecture_check`; zakończył odczyt AGENTS i audyt architektury. Definicja narzędzia przypisuje tej roli niezmienne `gpt-6-astra / medium`; raport agenta nie jest traktowany jako niezależny pomiar modelu. Zgodnie z instrukcją użytkownika ten test zamknął bramkę i pozwolił rozpocząć Etap 1. Nie zmieniano globalnego zaufania, uprawnień ani trybu sandboxa.

| Agent / zadanie | Model / reasoning z definicji roli | Zakres |
| --- | --- | --- |
| architecture_auditor / architecture_check | gpt-6-astra / medium | Zakończony test natywnej delegacji i audyt do odczytu |
| project_setup / setup_stage1 | gpt-6.1-terra / low | Bootstrap Qt, zależności, pytest.ini i izolacja DB w conftest |
| qa_reviewer / istniejący wątek QA | gpt-6-astra / medium | Przegląd kodu/testów, 11 wybranych testów oraz 4 testy po poprawce izolacji subprocessów |

Koordynator odpowiada za testy regresyjne, integrację, dokumentację i Git. Maksymalnie 2 subagentów poza koordynatorem; bez dalszego delegowania.

Próba otwarcia nowego wątku QA została odrzucona przez limit wątków agentów. Wykorzystano istniejącego `qa_reviewer` przez natywne `followup_task`; nie zwiększano limitu ani liczby równoległych wykonawców.

### Zakres implementacji

- Niezależny start `app/gui_app.py` oraz `app/gui/application.py`: QApplication, proste okno bootstrap QWidget, pętla Qt i polski komunikat błędu inicjalizacji bazy. Sam import nie uruchamia GUI i nie zapisuje bazy.
- Osobne pliki `requirements-gui.txt` (PySide6 6.12.0) i `requirements-dev.txt` (pytest 8.4.2), bez zmian dotychczasowego requirements.txt.
- Ostateczna mapa plików i odpowiedzialności w sekcji 5 planu; usługi/repozytoria i sesja pozostają istniejące. Kontrolery i worker I/O pojawią się wraz z odpowiednimi funkcjami, nie na zapas.
- `pytest.ini`, `tests/conftest.py`: importy przez `app/`, autouse podmiana `persistence.database.DB_PATH` na ścieżkę tymczasową; osobna fixture tworzy schemat tylko tam, gdzie jest potrzebny.
- Regresje: reguły wszystkich 9 BetType, zero i granice, wypłaty i saldo, walidacja/atomowość pakietu, CHIPS/LIFO/limit/tożsamość Bet, profile, transakcje rundy i sklepu, pending/retry, statystyki i wszystkie sortowania rankingu.
- Testy granic importów w świeżych procesach oraz smoke oryginalnego punktu wejścia TUI w trybie headless Textual i bootstrap Qt offscreen.
- Nie wdrażano profili GUI, nawigacji, stołu ani animacji. To zakres kolejnych etapów.

### Weryfikacja Etapu 1

- **Pełny zestaw: `573 passed in 3.64s`** po poprawkach QA, polecenie `.\venv\Scripts\python.exe -m pytest -q`. Wcześniejszy przebieg przed poprawką izolacji: 573 passed in 5.25s.
- Instalacja do projektowego venv: PySide6 6.12.0, Qt 6.12.0, pytest 8.4.2 na Python 3.10.6 / Windows x64. Textual 8.2.8 i Rich 15.0.0 pozostały bez zmian. Dwie próby pobierania metadanych w sandboxie nie zakończyły się; zostały przerwane. Instalacja po jednorazowym rozszerzeniu uprawnień polecenia zakończyła się poprawnie, bez zmiany globalnego sandboxa lub ustawień bezpieczeństwa.
- **`pip check`: No broken requirements found.**
- AST: 10 nowych plików Python poprawnych składniowo. `git diff --cached --check` i przegląd staged diffu bez problemów; commit implementacji zawiera wyłącznie 13 jawnie dodanych plików.
- TUI: wykonano oryginalny `app/app.py` z pętlą testową Textual, utworzenie profilu, otwarcie ekranu gry, powrót do menu, zachowanie sesji i blokady profilu/wyjścia przy zakładach. Nie jest to ręczny test terminala ani pełny audyt wizualny TUI.
- Qt: offscreen sprawdzono utworzenie/pokazanie/zamknięcie QWidget, rzeczywistą pętlę zdarzeń `run()`, inicjalizację tymczasowej bazy i obsługę błędu SQLite/OSError. Test pętli ma watchdog 5 sekund. Brak ręcznej oceny wyglądu i pełnej funkcjonalności GUI, która jeszcze nie istnieje.
- QA: pierwsza ocena wykazała P2 w izolacji bazy nowych procesów. Poprawiono prelude ustawiający DB_PATH przed badanymi importami i asercję braku zapisu. Po poprawce QA ponownie potwierdził 4 testy granic importów (0.71 s), watchdog i historyczny opis planu. **Brak pozostałych uwag blokujących.**
- Diff względem `954cc707e866067446fe8bf1084da673c8a31657` dla `app/domain/`, `app/services/`, `app/persistence/`, całego starego TUI i `requirements.txt` pusty. **Logika biznesowa, schemat i istniejące źródła TUI nie zostały zmienione.**
- Hash SHA-256 roboczej `data/roulette.db` po testach i QA identyczny z odczytem sprzed prac; baza nie jest częścią commita. Testy używają wyłącznie baz tymczasowych, również w subprocessach i próbie trybu frozen.
- Nie budowano EXE i nie wdrażano Etapu 2. Brak dalszych zadań w zakresie Etapu 1.

### Uruchomienie i ręczne sprawdzenie

Z katalogu repozytorium w PowerShell, z istniejącym projektowym venv:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-gui.txt -r requirements-dev.txt
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe app/gui_app.py
```

Po starcie GUI oczekiwane jest proste okno z nazwą Obsidian Royale, możliwe do zamknięcia standardowym przyciskiem okna. To bootstrap, bez wyboru profilu i rozgrywki. Normalny start korzysta z dotychczasowego `init_db()` i bazy `data/roulette.db`; testy są izolowane.

Dotychczasowy start TUI: `.\venv\Scripts\python.exe app/app.py`. Na świeżym środowisku najpierw zainstaluj również `requirements.txt`; nie jest zastępowany plikiem GUI. Nie uruchamiaj równoczesnej gry TUI i GUI tym samym profilem.

## Kluczowe decyzje i ograniczenia

- `Game` jest jedynym źródłem zakładów, salda sesji i limitów; `RoundResult` źródłem rozliczenia i wyniku koła.
- Nowy spin tylko przez `spin_and_save()`. Błąd zapisu: zachować sesję i użyć `save_pending_round()`; nie losować ponownie, nie odczytywać prywatnych pól.
- Blokady pending/animacji muszą być centralnie w kontrolerze. `GameSession` nie blokuje wszystkich operacji `Game`, a pending istnieje wyłącznie w pamięci.
- Brak synchronizacji równoczesnej gry TUI i GUI tym samym profilem. Nie zmieniamy silnika ani nie dodajemy takiej funkcji.
- Usuwanie pozycji wymaga tożsamości `Bet`; limit 5 odnosi się do CHIPS. Wszystkie 9 BetType mają pozostać dostępne.
- Importy pozostają `domain.*`, `services.*`, `persistence.*`; osobny skrypt startowy GUI nie może importować prezentacji TUI.
- Python 3.10.6, Textual 8.2.8, Rich 15.0.0. Etap 1 dodaje oddzielne zależności PySide6/pytest i zestaw testów; nie zmienia pakietów TUI w requirements.txt.
- Istniejące ignorowane pliki buildu/EXE pozostają nietknięte; nie zweryfikowano ich świeżości.
- Instrukcje zakresów plików agentów nie są technicznym sandboxem. Wspólne kontrolery wymagają sekwencyjnej integracji.
- Dawny problem z osobnym CLI nie blokuje natywnej delegacji w obecnej sesji. Nie traktować wyniku CLI innego konta jako dowodu o konfiguracji bieżącej sesji.

## Wznowienie i załadowanie konfiguracji

1. Otwórz ten sam projekt na `codex`; przeczytaj AGENTS, plan, dziennik i sprawdź status oraz HEAD. Nie klonuj repozytorium.
2. Przy nowej sesji sprawdź dostępność nazwanych ról w natywnym narzędziu delegacji. W razie wątpliwości wykonaj krótki audyt do odczytu przez `architecture_auditor`; nie diagnozuj bieżącej sesji wyłącznie przez osobny CLI.
3. Nie zmieniaj zaufania projektu, globalnych uprawnień ani sandboxa. Zachowaj model koordynatora GPT-6.1 Sol / High i limit 2 subagentów.
4. Po ukończeniu Etapu 1 dalsza praca wymaga dokładnie `ZATWIERDZAM ETAP 1 — PRZEJDŹ DO ETAPU 2`. Sama działająca delegacja nie zatwierdza kolejnych etapów.
5. Wykonać wyłącznie następny zaakceptowany etap, testy i kontrolę diffu, uzupełnić dziennik, commit i zatrzymać się.

## Następny etap — jeszcze nieautoryzowany

Etap 2: właściwe główne okno PySide6, nawigacja, tworzenie i wybieranie profili, menu oraz integracja z istniejącymi repozytoriami i GameSession. Do wykonania dopiero po akceptacji Etapu 1.
