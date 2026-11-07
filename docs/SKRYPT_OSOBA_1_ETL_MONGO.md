# Skrypt do omowienia projektu - Osoba 1

## Moja czesc projektu
Moja czesc obejmuje poczatek calego pipeline'u, czyli droge danych od internetu do lokalnego MongoDB.
W praktyce odpowiadam za:

- znalezienie plikow z danymi,
- przygotowanie listy plikow do pobrania,
- pobranie i rozpakowanie archiwow,
- czyszczenie danych,
- import do lokalnej bazy MongoDB,
- zabezpieczenie przed duplikacja przy ponownym uruchomieniu.

Najprosciej mowiac: ja odpowiadam za to, zeby surowe dane zamienily sie w uporzadkowany, gotowy do dalszego przetwarzania zbior lokalny.

## Jak wyglada przeplyw danych w mojej czesci
Kolejnosc jest taka:

1. `scripts/scrape_tripdata.py` scrapuje strone `https://citibikenyc.com/system-data` i buduje manifest archiwow do pobrania.
2. `bigdata_project/manifest.py` buduje manifest, czyli uporzadkowana liste plikow do pobrania.
3. `scripts/download_and_stage.py` korzysta z manifestu, pobiera archiwa `.zip` i rozpakowuje je do plikow `.csv`.
4. `bigdata_project/download.py` obsluguje samo pobieranie, wznowienie po bledzie, sprawdzanie archiwum i rozpakowanie.
5. `bigdata_project/transform.py` czyta CSV partiami i czysci dane.
6. `scripts/load_local_mongo.py` bierze oczyszczone dane i zapisuje je do lokalnego MongoDB.
7. `bigdata_project/mongo_ops.py` obsluguje polaczenie z MongoDB, indeksy, statusy importu i ochrone przed duplikatami.

## Co mowie o kazdym pliku

### `scripts/scrape_tripdata.py`
To jest skrypt startowy do zbudowania listy danych.
Jego rola jest prosta:

- bierze wybrane lata, na przyklad `2024,2025`,
- scrapuje oficjalna strone `system-data`,
- zapisuje raport z tego scrapingu do `outputs/system_data_scrape.json`,
- uruchamia budowanie manifestu,
- zapisuje wynik do pliku JSON.

Czyli to nie pobiera jeszcze samych danych, tylko najpierw tworzy plan: jakie pliki mamy pobrac.

### `bigdata_project/manifest.py`
To jest logika odpowiedzialna za manifest.
Ten plik:

- laczy sie ze strona `system-data` i wyciaga z niej link do danych trip history,
- korzysta z tego jako jawnego etapu scrapingu,
- dopiero potem odczytuje liste archiwow `.zip`,
- odfiltrowuje tylko miesieczne pliki Citi Bike,
- zapisuje dla nich informacje takie jak rok, miesiac i URL,
- tworzy plik manifestu w JSON.

To jest wazne, bo dzieki temu dalsze skrypty nie musza zgadywac, co pobierac. One po prostu czytaja gotowa liste.

W tym pliku jest tez funkcja do filtrowania wpisow, wiec mozemy uruchamiac pipeline dla calego zakresu albo tylko dla jednego miesiaca.

### `scripts/download_and_stage.py`
Ten skrypt realizuje etap stagingu danych.
On:

- wczytuje manifest,
- wybiera wpisy z wybranego roku lub miesiaca,
- pobiera odpowiednie archiwa,
- rozpakowuje je do folderu z surowymi CSV,
- zapisuje prosty raport stagingu.

To jest moment, w ktorym dane przechodza z internetu na nasz komputer.

### `bigdata_project/download.py`
Tutaj jest techniczna obsluga pobierania i rozpakowania.
Najwazniejsze rzeczy:

- pobieranie odbywa sie strumieniowo, a nie wszystko naraz do RAM,
- skrypt obsluguje kilka prob w razie bledu sieci,
- plik najpierw zapisuje sie jako `.part`, a dopiero potem jako finalne `.zip`,
- jesli archiwum juz istnieje i jest poprawne, nie pobieramy go drugi raz,
- rozpakowanie tez jest bezpieczne i nie nadpisuje niepotrzebnie gotowych plikow.

To jest wazne dla stabilnosci i dla ponownego uruchamiania.

### `bigdata_project/transform.py`
To jest jeden z najwazniejszych plikow w mojej czesci, bo tu odbywa sie czyszczenie danych.

Ten plik:

- czyta CSV partiami, zeby nie ladowac wszystkiego naraz do pamieci,
- sprawdza, czy sa wymagane kolumny,
- zamienia daty na poprawny format czasu,
- usuwa rekordy bez kluczowych danych,
- usuwa rekordy, gdzie koniec przejazdu jest wczesniej niz poczatek,
- liczy czas przejazdu w minutach,
- odrzuca bardzo podejrzane przejazdy, na przyklad dluzsze niz 24 godziny,
- uzupelnia braki tekstowe wartoscia `unknown`,
- zamienia wspolrzedne na liczby,
- odrzuca rekordy spoza przyjetego obszaru Nowego Jorku,
- dodaje pola pomocnicze, na przyklad rok, miesiac, dzien tygodnia, godzine i nazwe pliku zrodlowego.

Czyli nie wrzucamy do bazy surowych danych 1:1, tylko dane juz uporzadkowane i ujednolicone.

### `scripts/load_local_mongo.py`
To jest skrypt, ktory bierze przetworzone dane i laduje je do lokalnego MongoDB.

On:

- laczy sie z lokalna baza,
- przygotowuje indeksy,
- sprawdza manifest i wybiera pliki do importu,
- dla kazdego CSV czyta dane partiami,
- dla kazdej partii wywoluje czyszczenie z `transform.py`,
- zamienia wiersze DataFrame na dokumenty MongoDB,
- zapisuje je do kolekcji lokalnej,
- zapisuje informacje o statusie importu i prosty raport jakosci danych.

To jest glowny etap, dzieki ktoremu spelniony jest wymog pracy z lokalnym MongoDB.

### `bigdata_project/mongo_ops.py`
Ten plik zawiera operacje bazodanowe.
Najwazniejsze rzeczy:

- `get_local_database()` laczy nas z lokalnym MongoDB,
- `ensure_local_indexes()` zaklada indeksy dla metadanych importu,
- `ensure_trip_indexes()` zaklada indeksy dla danych o przejazdach,
- `record_import_status()` zapisuje status danego pliku,
- `start_import_run()` i `finish_import_run()` zapisuje metadane calego uruchomienia,
- `insert_cleaned_documents()` robi `upsert`, a nie zwykle `insert`,
- `create_quality_report()` zapisuje ile wierszy weszlo i ile odpadlo.

## Jak dziala zabezpieczenie przed duplikacja
To jest bardzo wazne, bo to jest tez wymaganie na `4.0` i wyzej.

Mamy tu dwa mechanizmy:

### 1. Status zaimportowanego pliku
W kolekcji `imported_files` zapisujemy status konkretnego archiwum.
Jesli plik byl juz oznaczony jako `loaded_local_mongo`, to skrypt moze go pominac przy kolejnym uruchomieniu.

### 2. Upsert po sztucznym `_id`
Kazdy dokument ma `_id` zbudowane jako:

`ride_id::source_file`

To oznacza, ze nawet jesli skrypt uruchomimy drugi raz, rekord nie powinien zostac powielony.
Zamiast duplikatu nastapi aktualizacja tego samego dokumentu.

## Jak ta czesc laczy sie z reszta projektu
Moja czesc przygotowuje dane dla nastepnych etapow.

To, co ja robie, daje:

- surowe CSV w folderach lokalnych,
- oczyszczone dane w lokalnym MongoDB,
- gotowy punkt startowy dla dalszych analiz,
- ta sama logike czyszczenia, ktora jest potem wykorzystywana tez przy przygotowaniu plikow do HDFS.

To jest wazne, bo dzieki temu nie mamy dwoch roznych wersji danych: jedna logika czyszczenia sluzy i do MongoDB, i do dalszego etapu big data.

## Jak moge to opowiedziec na konsultacji
Przykladowo moge powiedziec tak:

"Moja czesc projektu obejmuje ETL i lokalna baze. Najpierw skrypt buduje manifest plikow ze strony Citi Bike, potem pobiera archiwa ZIP i rozpakowuje CSV. Nastepnie dane sa czytane partiami i czyszczone: usuwamy bledne rekordy, liczymy czas przejazdu, uzupelniamy braki oraz odrzucamy rekordy spoza przyjetego obszaru. Na koncu zapisujemy dane do lokalnego MongoDB. Import jest idempotentny, bo zapisujemy statusy plikow oraz stosujemy upsert po sztucznym identyfikatorze dokumentu."

## O co moga zapytac i jak odpowiedziec

### Po co manifest?
Manifest oddziela etap wykrycia danych od etapu pobierania. Dzieki temu wiemy dokladnie, jakie pliki sa w zakresie projektu i mozemy latwo filtrowac po roku i miesiacu.

### Czemu czytacie dane partiami?
Bo dane sa duze. Czytanie partiami zmniejsza zuzycie pamieci i pozwala stabilniej obrabiac wiele gigabajtow danych.

### Po co czyszczenie?
Bo dane z praktyki moga miec braki, bledne daty albo nietypowe wartosci. Bez czyszczenia analizy bylyby mniej wiarygodne.

### Jak unikacie duplikatow?
Przez zapisywanie statusu importu plikow oraz przez `upsert` z wlasnym `_id`.

### Co trafia do lokalnego MongoDB?
Nie surowe ZIP-y, tylko oczyszczone rekordy przejazdow oraz metadane importu i raporty jakosci.

## Najwazniejsze zdanie do zapamietania
Moja rola polega na tym, zeby pobrac dane, uporzadkowac je i bezpiecznie zapisac do lokalnego MongoDB tak, aby dalsze etapy projektu pracowaly juz na stabilnym, oczyszczonym zbiorze.

## Krotkie streszczenie do powiedzenia
"W naszej czesci projektu odpowiadam za ETL i lokalne MongoDB. Najpierw pobieramy ze strony Citi Bike liste plikow, czyli manifest, a potem sciagamy archiwa ZIP i rozpakowujemy je do CSV. Nastepnie dane sa czytane partiami i czyszczone: sprawdzamy wymagane kolumny, usuwamy bledne rekordy, liczymy czas przejazdu i uzupelniamy braki. Na koncu zapisujemy oczyszczone dane do lokalnego MongoDB. Bardzo wazne jest to, ze import mozna uruchamiac ponownie bez niekontrolowanego duplikowania rekordow, bo zapisujemy statusy plikow oraz stosujemy upsert po wlasnym identyfikatorze dokumentu. Dzieki temu dalsza czesc projektu pracuje juz na danych uporzadkowanych i gotowych do analiz."
