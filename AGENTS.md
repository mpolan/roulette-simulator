# Obsidian Royale — zasady migracji GUI

## Zakres i akceptacja

- Pracuj w istniejącym repozytorium, wyłącznie na gałęzi `codex`. Nie klonuj projektu.
- Przed pracą przeczytaj `docs/GUI_MIGRATION_PLAN.md`, `docs/GUI_PROGRESS.md`, sprawdź katalog, gałąź, status i ostatni commit. Zachowuj wcześniejsze zmiany użytkownika.
- Realizuj tylko zaakceptowany etap. Po każdym etapie wykonaj przegląd diffu, odpowiednie kontrole, aktualizację dziennika, logiczny commit i zatrzymaj się.
- Etap 0 jest zlecony; Etapy 1–9 wymagają kolejnych akceptacji. Przejście jest dozwolone wyłącznie po wiadomości `ZATWIERDZAM ETAP X — PRZEJDŹ DO ETAPU X+1`. Pytania i sugestie nie są akceptacją.
- Raport zawiera zakres, agentów/model/rozumowanie, pliki, wyniki kontroli i ograniczenia, stan zamrożonej logiki, SHA, instrukcję sprawdzenia oraz zakres kolejnego etapu. Kończ raport: `ETAP X ZAKOŃCZONY — OCZEKUJĘ NA TWOJE ZATWIERDZENIE.`
- Komunikacja i dokumentacja użytkownika po polsku. Conventional Commits po angielsku.

## Nienaruszalna warstwa silnika

- Nie zmieniaj `app/domain/`, `app/services/`, `app/persistence/`. Jeśli zmiana okaże się niezbędna, zatrzymaj tę pracę, uzasadnij i uzyskaj osobną zgodę użytkownika.
- Zachowaj TUI i jego punkt wejścia `python app/app.py`. Nie przenoś ani nie przemianowuj jego modułów.
- GUI używa tych samych `Game`, `GameSession`, usług i repozytoriów oraz obecnego schematu SQLite. Nie pisz drugiego resolvera, walidatora, generatora wyników, statystyk, rankingu ani sklepu.
- GUI wywołuje `GameSession.spin_and_save()` raz dla nowej rundy. Animacja korzysta wyłącznie z zwróconego `RoundResult`. Błąd zapisu oznacza `save_pending_round()` na tej samej sesji, bez kolejnego losowania i bez dostępu do prywatnych pól sesji.
- Zachowuj tożsamość obiektów `Bet` przy usuwaniu; grupowanie jest wyłącznie prezentacją. Kwoty, limity i stan stosów czytaj z `Game`.
- Blokuj niedozwolone interakcje podczas animacji, aktywnych zakładów i oczekiwania na zapis zgodnie z kontraktami opisanymi w planie. Nie gub sesji przy nawigacji.
- Nie modyfikuj roboczej bazy ani nie uruchamiaj seedera w ramach testów. Testy persystencji używają tymczasowej bazy i izolują `persistence.database.DB_PATH` wyłącznie na czas testu.

## Architektura i UI

- Python + PySide6, Qt Widgets; QGraphicsScene/QGraphicsView dla stołu i koła, gdy uzasadnia to interakcja.
- Prosty podział: widoki, kontrolery prezentacji i istniejący silnik. Nie dodawaj zbędnych usług domenowych.
- Nowe pliki GUI docelowo w `app/gui/`, niezależny start `app/gui_app.py`. Ostateczną strukturę i zależności ustala dopiero Etap 1.
- Motyw Obsidian Royale: ciemne tło, złote akcenty, czytelne pola i żetony, mysz i klawiatura.
- Sygnały/sloty, trwałe widgety i aktualizacje konkretnych pól. Bez przebudowy całego drzewa po każdej zmianie, `time.sleep()`, blokujących pętli animacji lub dodatkowego losowania.
- Nie dodawaj typów zakładów ani funkcji spoza istniejącego zakresu. Obecne API nie obejmuje split/street/corner/six-line.

## Agenci i integracja

- Koordynator: `gpt-6.1-sol`, `high`. Konfiguracja projektu: `.codex/config.toml`; 11 samodzielnych definicji w `.codex/agents/`.
- Maksymalnie 2 jednocześnie aktywnych subagentów, poza koordynatorem. Nie zlecaj subagentom dalszego delegowania. Dodatkową równoległość wolno rozważyć tylko przy udokumentowanym niezależnym zadaniu; nie zmieniaj limitu samowolnie.
- Wybierz rolę pasującą do etapu. Audytorzy pracują tylko do odczytu; koordynator integruje i wykonuje commity.
- Przed uruchomieniem sprawdź model i reasoning w katalogu środowiska. Brak obsługi zgłoś, zaproponuj odpowiednik i nie zastępuj modelu po cichu.
- Każde zlecenie zawiera etap, cel, model/rozumowanie, dozwolone pliki i zakazy. Przy braku narzędzia wyboru nazwanej roli odczytaj jej TOML, przekaż instrukcje jawnie i odnotuj tę różnicę.
- Zakresy w instrukcjach agentów są regułami współpracy, nie osobnymi sandboxami systemowymi. Wspólne pliki kontrolerów przydzielaj jednemu wykonawcy na raz.

## Git i weryfikacja

- Bez merge, rebase, push, destrukcyjnego resetu, zmian `main`/`dev` i nadpisywania plików użytkownika.
- Commituj tylko jawnie wymienione pliki danego etapu, nigdy bezrefleksyjnie `git add .`.
- Przed commitem: `git diff --check`, przegląd staged diffu, kontrola braku zmian w zamrożonych katalogach i TUI. Po commicie sprawdź SHA i status.
- Stosuj kontrole adekwatne do etapu. Etap 0 sprawdza dokumentację, konfigurację i integralność źródeł; testy bazowe i uruchomienie TUI należą do Etapu 1.
- Nie utożsamiaj audytu statycznego z działającym GUI, testem TUI ani sprawdzeniem świeżego EXE.
- Nie commituj baz, danych prywatnych, poświadczeń, środowiska wirtualnego ani artefaktów wydania.
