# Obsidian Royale — dziennik migracji GUI

## Stan i bramka akceptacji

- Aktualizacja: 2026-11-15.
- Aktualnie zaakceptowany etap: **brak zakończonego etapu zaakceptowanego przez użytkownika**. Zlecono realizację wyłącznie Etapu 0.
- Etap 0: **ukończony; oczekiwanie na akceptację użytkownika**.
- Etap 1 i dalsze: **nierozpoczęte**. Nie implementowano GUI, nie instalowano Qt.
- Gałąź: `codex`; początkowy commit: `4ba0069f25eb652917a039f76c634fdd1d8d4072` (`Roulette MVP 3.0`). Początkowy status czysty, brak wcześniejszych zmian użytkownika.
- Ostatni commit konfiguracji: `7c5bacfcebe0bf0af4fbbcc4d40d39e2a1e9de38` — `chore(gui): configure project agents` (13 plików: AGENTS i konfiguracja ról).
- Ostatni commit dokumentacji: commit zawierający ten dziennik, do ustalenia przez `git log -1 --format="%H %s" -- docs/GUI_PROGRESS.md`. Jego SHA zostanie podany w raporcie czatu. Własnego SHA nie wpisujemy do treści tego samego commita, aby uniknąć samoodwołania.
- Kontynuacja wyłącznie po: `ZATWIERDZAM ETAP 0 — PRZEJDŹ DO ETAPU 1`.

| Etap | Stan | Akceptacja |
| --- | --- | --- |
| 0 — Bootstrap i audyt | Ukończony | Oczekiwana po raporcie |
| 1 — Testy bazowe i architektura | Nierozpoczęty | Brak |
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

## Faktycznie użyci agenci

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

## Kluczowe decyzje i ograniczenia

- `Game` jest jedynym źródłem zakładów, salda sesji i limitów; `RoundResult` źródłem rozliczenia i wyniku koła.
- Nowy spin tylko przez `spin_and_save()`. Błąd zapisu: zachować sesję i użyć `save_pending_round()`; nie losować ponownie, nie odczytywać prywatnych pól.
- Blokady pending/animacji muszą być centralnie w kontrolerze. `GameSession` nie blokuje wszystkich operacji `Game`, a pending istnieje wyłącznie w pamięci.
- Brak synchronizacji równoczesnej gry TUI i GUI tym samym profilem. Nie zmieniamy silnika ani nie dodajemy takiej funkcji.
- Usuwanie pozycji wymaga tożsamości `Bet`; limit 5 odnosi się do CHIPS. Wszystkie 9 BetType mają pozostać dostępne.
- Importy pozostają `domain.*`, `services.*`, `persistence.*`; osobny skrypt startowy GUI nie może importować prezentacji TUI.
- Python 3.10.6, Textual 8.2.8, Rich 15.0.0; brak PySide6, pytest i istniejącego zestawu testów. Zależności dobierze Etap 1.
- Istniejące ignorowane pliki buildu/EXE pozostają nietknięte; nie zweryfikowano ich świeżości.
- Instrukcje zakresów plików agentów nie są technicznym sandboxem. Wspólne kontrolery wymagają sekwencyjnej integracji.
- Osobny CLI wewnątrz sandboxa pomija konfigurację niezaufanego projektu. Nie utożsamiać poprawnego TOML/strict startup z potwierdzonym efektywnym modelem i limitem w aplikacji desktopowej.

## Wznowienie i załadowanie konfiguracji

Nowe TOML nie zmieniają potwierdzonych ustawień już działającego czatu. Aby kolejne etapy rozpocząć z konfiguracją projektu:

1. Po raporcie Etapu 0 zamknij i uruchom ponownie aplikację Codex, otwórz ten sam lokalny projekt i rozpocznij nowy czat. Nie twórz nowego checkoutu ani nie klonuj repozytorium.
2. Wybierz GPT-6.1 Sol i rozumowanie High, jeżeli ustawienia projektu nie zostaną zastosowane automatycznie. Projekt musi być zaufany; nie zmieniaj globalnych uprawnień ani trybu sandboxa.
3. W nowym czacie wskaż `AGENTS.md`, `docs/GUI_MIGRATION_PLAN.md`, `docs/GUI_PROGRESS.md` i przekaż dokładnie `ZATWIERDZAM ETAP 0 — PRZEJDŹ DO ETAPU 1`, jeśli akceptujesz wynik.
4. Koordynator przed pracą sprawdza Git, modele, dostępne narzędzie delegacji i efektywną konfigurację/limit 2. Jeśli narzędzie nie wybiera nazwanej roli, jawnie odczytuje właściwy TOML i przekazuje jego ustawienia oraz zakres. Nie deklaruje automatycznego wczytania bez potwierdzenia.
5. Wykonać tylko Etap 1, uzupełnić dziennik, commit i ponownie zatrzymać się do akceptacji.

To ostrożna procedura załadowania nowej konfiguracji, a nie potwierdzenie jej przeładowania w tym czacie. Instrukcja wynika z bramki podanej przez użytkownika. Źródła formatu konfiguracji podano w planie.

## Następny etap — jeszcze nieautoryzowany

Etap 1: testy bazowe zamrożonej logiki na tymczasowych danych, ostateczny układ GUI, osobny punkt wejścia, zależności Qt i testowe oraz sprawdzenie działania istniejącego TUI. Do wykonania dopiero po wyraźnej akceptacji.
