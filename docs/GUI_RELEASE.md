# Obsidian Royale GUI — budowanie wydania

## Powtarzalny build Windows

Z katalogu projektu uruchom w PowerShell:

```powershell
.\build-gui.ps1
```

Skrypt instaluje zależności z `requirements-build-gui.txt`, w tym PyInstaller 6.22.3 i pakiety GUI, a następnie buduje aplikację według `ObsidianRoyaleGUI.spec`. Jeśli zależności są już zainstalowane, można pominąć instalację przez `.\build-gui.ps1 -SkipInstall`. Wynikiem jest `dist/ObsidianRoyaleGUI.exe`, zbudowany bez konsoli. Build nie uruchamia seedera i nie dołącza roboczej bazy ani demonstracyjnych danych.

## Baza danych i ochrona danych

Przy pierwszym uruchomieniu EXE publiczne `init_db()` tworzy pustą bazę `data/roulette.db` obok pliku wykonywalnego. Istniejący plik bazy jest zachowywany i używany ponownie. Nie kopiuj roboczej bazy do wydania, jeśli nie chcesz udostępnić jej profili i historii. Przed aktualizacją aplikacji zachowaj kopię bazy użytkownika; nie usuwaj jej w ramach aktualizacji EXE.

GUI i TUI są osobnymi punktami wejścia, ale korzystają ze wspólnych profili i bazy, gdy uruchomione ze źródeł w tym samym projekcie. Nie używaj równolegle tego samego profilu w obu aplikacjach.

## Kontrola wydania

Po zbudowaniu uruchom EXE na maszynie docelowej bez zależności środowiska deweloperskiego. Sprawdź utworzenie pustej bazy w lokalizacji obok EXE, utworzenie profilu, rozpoczęcie rundy, zapis rundy, zamknięcie oraz ponowny start z zachowaniem profilu. Osobno sprawdź działanie na kopii istniejącej bazy. Zapisz wynik testów i SHA pliku wykonywalnego w raporcie wydania.

Ta instrukcja opisuje procedurę budowania i kontroli; sama w sobie nie stanowi potwierdzenia poprawności świeżo zbudowanego pliku EXE.

## Zweryfikowane wydanie — 2026-11-16

- Windows 10 x64, Python 3.10.6, PySide6 6.12.0, PyInstaller 6.22.3. Pełna regresja: **710 passed in 49.45s**, w tym smoke Textual i testy SQLite/zakupów. Nie powtarzano całego zestawu.
- Finalny EXE: 48 630 117 bajtów; SHA-256 `3C85965F3BDBE9238172457A411BE476C7DE27C38961CDB2966264BAE5CAC624`. Sprawdzono PE Windows GUI (bez konsoli) i brak baz/danych demo w archiwum.
- Natywny test kopii finalnego EXE w odizolowanym folderze: utworzenie pustej bazy i profilu, żeton 25$, SPIN, wynik 29/czarne, saldo 975$, zamknięcie i ponowne uruchomienie z zachowanym profilem. Odczyt repozytorium potwierdził jedną zapisaną rundę 29. Zakupy i ich trwałość pokrywa pełna regresja; nie wykonano końcowego zakupu ręcznie w EXE.
- Test używał klawiatury i drzewa dostępności Windows. Przechwycenie obrazu przez pomocnika zgłosiło timeout; nie jest to pełna ocena wizualna ani test na czystej maszynie bez środowiska deweloperskiego.
- Pierwszy build miał konflikt bibliotek: PyInstaller pobrał `icuuc.dll` i `icudt78.dll` z zewnętrznego Popplera obecnego w PATH, zamiast użyć systemowej biblioteki ICU Windows. Porównano faktycznie ładowaną bibliotekę w źródłach; po usunięciu tych obcych plików z kopii diagnostycznej Qt ładowało się poprawnie. Finalny spec wyklucza te biblioteki ICU, a nowy EXE uruchomiono ponownie. Bez zmian silnika.

Do ręcznej kontroli wydania: uruchom EXE w zapisywalnym folderze, utwórz profil, postaw kilka żetonów, wykonaj SPIN, sprawdź statystyki/ranking i zamknij. Uruchom ponownie i sprawdź zachowaną historię. Przy profilu z odpowiednim saldem kup odznakę, sprawdź kolekcję po restarcie. Nie usuwaj folderu data przy aktualizacji.
