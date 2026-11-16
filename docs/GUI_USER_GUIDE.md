# Obsidian Royale GUI — skrócona instrukcja

## Uruchomienie i profile

W katalogu projektu uruchom `.\venv\Scripts\python.exe app/gui_app.py`. Wybierz istniejący profil albo utwórz nowy. GUI i TUI używają tej samej bazy danych; zamknij drugą instancję, jeśli oba interfejsy miałyby jednocześnie używać tego samego profilu.

## Gra

- Stół europejskiej ruletki zawiera pola 0–36 oraz obsługiwane typy zakładów. W trybie **CHIPS** wybierz nominał 5, 10, 25, 50 lub 100 i kliknij pole; limit wynosi pięć żetonów na pole. Prawy przycisk myszy usuwa ostatni żeton z pola.
- **Alt+1…5** wybiera nominał, **Alt+C** przełącza tryb CHIPS/CLASSIC.
- W trybie **CLASSIC** wybierz typ i stawkę. **Ctrl+Enter** zatwierdza zakład lub pakiet wybranych liczb.
- Na stole strzałki zmieniają zaznaczone pole; **Enter/Spacja** stawia żeton albo zatwierdza akcję, a **Delete** usuwa ostatni żeton. W koszyku **Delete/Backspace**, dwuklik lub przycisk **Usuń** usuwa jeden ostatni pierwotny zakład z wybranej grupy i zwraca jego stawkę. Grupowanie koszyka i wyniku jest wyłącznie prezentacją.
- **Ctrl+Spacja** uruchamia SPIN. GUI animuje wyłącznie wynik zwrócony przez istniejący silnik. Kolor zielony oznacza wygrany zakład, czerwony — przegrany.
- Jeśli zapis rundy się nie powiedzie, **Ctrl+R** lub **Ponów zapis** ponawia zapis tej samej rundy. Do udanego zapisu obstawianie i wyjście pozostają zablokowane.
- **Esc** wraca do menu. **Ctrl+Q** zamyka aplikację; **Alt+F4** i systemowy przycisk zamknięcia działają tak samo. Przy aktywnych zakładach można anulować je i zamknąć albo wrócić do gry.

## Pozostałe ekrany

Menu udostępnia statystyki gracza i kolekcję odznak, leaderboard z kryteriami sortowania oraz Prestige Shop. Dane pobierają istniejące usługi aplikacji. Odznaki są kosmetyczne.
