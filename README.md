# Obsidian Royale

Projekt zawiera dwie aplikacje korzystające z tego samego silnika ruletki i tej samej bazy SQLite:

1. **Projekt 1 — TUI**: dotychczasowy interfejs terminalowy oparty na Textual.
2. **Projekt 2 — GUI**: interfejs okienkowy PySide6, uruchamiany niezależnie od TUI.

GUI używa tych samych klas `Game`, `GameSession`, usług i repozytoriów. Nie zawiera osobnego generatora wyniku ani logiki rozliczania. Koło wyświetla wynik zwrócony przez `GameSession`; w razie błędu zapisu można ponowić zapis tej samej rundy. Widoki odświeżają zmienione elementy zamiast budować interfejs od nowa.

## Wymagania

- Windows i Python 3.10 lub nowszy.
- Dla uruchamiania ze źródeł: zależności TUI z `requirements.txt`; GUI dodatkowo wymaga `requirements-gui.txt`.
- Dla budowania wersji GUI: PowerShell i `requirements-build-gui.txt`.

## Uruchomienie gotowego EXE

Skopiuj `dist/ObsidianRoyaleGUI.exe` do zapisywalnego folderu i uruchom dwuklikiem.
Python ani osobna instalacja Qt nie są potrzebne. Program działa bez okna konsoli.
Dane zapisuje w `data/roulette.db` obok EXE; aktualizując program, zachowaj ten folder.

## Technologie i architektura

Python, Textual/Rich (TUI), PySide6/Qt Widgets (GUI), SQLite i PyInstaller (wydanie Windows).
Oba interfejsy są warstwami prezentacji nad niezmienionymi `domain/`, `services/` i `persistence/`.
GUI ma osobne widoki, kontrolery prezentacji oraz jeden worker Qt do operacji danych.
`GameSession.spin_and_save()` losuje, rozlicza i zapisuje rundę; animacja dostaje gotowy `RoundResult`
i jedynie zatrzymuje koło na jego wyniku. Ponowienie zapisu nie losuje ponownie.
Stół porównuje stan poszczególnych pól, koszyk zachowuje wiersze i oryginalne obiekty zakładów,
a sklep aktualizuje istniejące karty — bez odtwarzania całego ekranu.

## Uruchamianie ze źródeł

W PowerShell, w katalogu projektu:

```powershell
# Projekt 1: TUI
.\venv\Scripts\python.exe app/app.py

# Projekt 2: GUI
.\venv\Scripts\python.exe app/gui_app.py
```

Jeśli środowisko nie jest przygotowane, utwórz je i zainstaluj potrzebne zależności:

```powershell
py -3.10 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-gui.txt
```

Uruchomienie TUI pozostaje niezależne od PySide6; do samego TUI wystarcza dotychczasowy `requirements.txt`.

## Dane gracza

Wersja uruchamiana ze źródeł korzysta z `data/roulette.db` w katalogu projektu. Wersja GUI zbudowana jako EXE używa `data/roulette.db` obok pliku wykonywalnego. Przy pierwszym uruchomieniu GUI tworzy pusty schemat bazy, bez profili demonstracyjnych. Istniejącej bazy nie nadpisuje. Zachowaj kopię pliku bazy przed ręcznym przenoszeniem lub usuwaniem danych. Nie uruchamiaj narzędzia seedującego na bazie zawierającej dane użytkownika.

## Wydanie GUI

Instrukcję budowania i sprawdzenia znajdziesz w [docs/GUI_RELEASE.md](docs/GUI_RELEASE.md), a skróconą instrukcję sterowania w [docs/GUI_USER_GUIDE.md](docs/GUI_USER_GUIDE.md). Plan migracji i dziennik etapów są w `docs/GUI_MIGRATION_PLAN.md` oraz `docs/GUI_PROGRESS.md`.
