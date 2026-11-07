# Skrypt do omowienia projektu - Osoba 2

## Moja czesc projektu
Moja czesc zaczyna sie tam, gdzie dane sa juz pobrane i oczyszczone, a konczy na wynikach analizy.
Odpowiadam za:

- przygotowanie danych do HDFS,
- upload do HDFS,
- konfiguracje Hadoop Streaming pod Pythona,
- uruchamianie MapReduce,
- zapis wynikow do MongoDB Atlas,
- lokalne analizy statystyczne,
- dashboard z wizualizacja.

Najprosciej mowiac: ja odpowiadam za warstwe big data i za pokazanie wynikow.

## plik bootstrap.py 
Jest po to, żeby skrypty uruchamiane z folderu scripts mogły importować wspólne moduły projektu, np. konfigurację i logikę ETL.

## plik config.py
config.py jest centralnym miejscem konfiguracji projektu. Zbiera ścieżki do danych, ustawienia MongoDB i HDFS oraz zmienne z pliku .env, dzięki czemu wszystkie skrypty korzystają z tych samych ustawień.

## Jak wyglada przeplyw danych w mojej czesci
Kolejnosc jest taka:

1. `scripts/push_to_hdfs.py` wrzuca pobrane archiwa ZIP do HDFS jako glowny zbior danych.
2. `bigdata_project/hdfs_ops.py` wrzuca archiwa ZIP i pliki robocze do HDFS przez WebHDFS.
3. `docker-compose.yml` uruchamia lokalne srodowisko z NameNode, DataNode i MongoDB.
4. `docker/hadoop-python/Dockerfile` dodaje `python3` do kontenerow Hadoop, zeby dzialal Streaming w Pythonie.
5. `scripts/prepare_mapreduce_input.py` przygotowuje tymczasowe wejscie TSV do Hadoop Streaming.
6. `scripts/run_mapreduce.py` uruchamia job Hadoop Streaming.
7. `hadoop/mapper.py` zamienia kazdy przejazd na pary klucz-wartosc do analiz.
8. `hadoop/reducer.py` laczy wyniki i liczy agregaty koncowe.
9. `scripts/load_results_atlas.py` zapisuje wyniki do MongoDB Atlas.
10. `scripts/run_local_analysis.py` tworzy proste lokalne statystyki do dashboardu.
11. `scripts/verify_month.py` porownuje wynik Hadoop z wynikiem referencyjnym z Pandas dla jednego miesiaca.
12. `app/dashboard.py` pokazuje wykresy i tabele.

## Co mowie o kazdym pliku

### `scripts/push_to_hdfs.py`
Ten skrypt odpowiada za glowny zbior danych w HDFS.
On:

- czyta pobrane archiwa z `data/raw/zip/`,
- wrzuca te archiwa do HDFS,
- zapisuje je w katalogu `raw`.

Wazne jest to, ze po poprawce glowny zbior w HDFS to archiwa ZIP, zgodnie z uwaga prowadzacego.

### `scripts/prepare_mapreduce_input.py`
To jest dodatkowy etap roboczy przed Hadoop Streaming.
On:

- pobiera ZIP-y z `HDFS/raw`,
- rozpakowuje je roboczo,
- stosuje te sama logike czyszczenia co ETL,
- przygotowuje pliki TSV tylko pod uruchomienie joba,
- wrzuca je do tymczasowej sciezki w HDFS, czyli `processed_tmp`.

To jest wazne, bo Hadoop Streaming potrzebuje wygodnego wejscia tekstowego, ale nie traktujemy juz tych TSV jako glownego zbioru w HDFS.

### `bigdata_project/hdfs_ops.py`
To jest warstwa komunikacji z HDFS przez WebHDFS.
Ten plik:

- tworzy katalogi w HDFS,
- wysyla pliki do HDFS,
- korzysta z ustawien z `.env`,
- pilnuje poprawnego uzytkownika HDFS.

Przy naszym setupie w Dockerze wazne jest ustawienie:

`HDFS_USER=root`

Bez tego mozna dostac blad uprawnien przy zapisie do HDFS.

### `docker-compose.yml`
Ten plik uruchamia cala infrastrukture lokalna.
W projekcie sa tam:

- lokalne MongoDB,
- Hadoop NameNode,
- Hadoop DataNode.

To jest podstawa calego srodowiska, bo bez tych kontenerow nie ma ani lokalnej bazy, ani HDFS.

### `docker/hadoop-python/Dockerfile`
Ten plik rozwiazuje wazny problem techniczny:
standardowy obraz Hadoop nie mial gotowego `python3`, a Hadoop Streaming mial uruchamiac nasze skrypty Pythona.

Dlatego ten Dockerfile:

- buduje obraz na bazie gotowych obrazow Hadoop,
- instaluje `python3`,
- pozwala odpalac mapper i reducer w Pythonie wewnatrz kontenera.

To jest kluczowe dla wymagania `5.0`, bo nasz MapReduce jest w Pythonie przez Hadoop Streaming.

### `scripts/run_mapreduce.py`
To jest glowny skrypt uruchamiajacy job MapReduce.
On:

- kopiuje `mapper.py` i `reducer.py` do kontenera NameNode,
- sprawdza, czy w kontenerze jest `python3`,
- buduje komende Hadoop Streaming,
- uruchamia job na danych z tymczasowej sciezki `processed_tmp` w HDFS,
- zbiera logi i podstawowe liczniki joba,
- pobiera wynik z HDFS do lokalnego pliku `outputs/mapreduce_results.tsv`.

Czyli to jest warstwa uruchomieniowa dla analizy big data.

### `hadoop/mapper.py`
Mapper czyta dane linia po linii z TSV.
Kazdy wiersz opisuje jeden przejazd.

Mapper tworzy klucze dla roznych analiz, na przyklad:

- liczba przejazdow per miesiac,
- sredni czas przejazdu per typ klienta,
- liczba przejazdow per typ roweru,
- liczba przejazdow per dzien tygodnia,
- liczba przejazdow per stacja startowa,
- liczba przejazdow per godzina i typ klienta.

Kazdy rekord jest zamieniany na czesciowe statystyki, ktore potem reducer laczy.

### `hadoop/reducer.py`
Reducer zbiera dane o tym samym kluczu i liczy wynik koncowy.
U nas dla kazdej grupy liczone sa:

- liczba rekordow,
- suma czasu przejazdow,
- sredni czas,
- odchylenie standardowe.

To jest wazne, bo dzieki temu nie tylko liczymy ile bylo przejazdow, ale tez opisujemy ich charakter.

### `scripts/load_results_atlas.py`
Ten skrypt bierze wynik z pliku `outputs/mapreduce_results.tsv` i zapisuje go do MongoDB Atlas.

On:

- czyta linie wynikowe z reducera,
- zamienia je na dokumenty JSON,
- zapisuje je do kolekcji w Atlasie,
- robi to przez `upsert`, czyli bez niekontrolowanego dublowania,
- zapisuje tez lokalny podglad wynikow do `atlas_results_preview.json`.

To spelnia wymaganie, zeby wyniki analiz, agregaty lub metadane byly zapisywane w MongoDB.

### `scripts/run_local_analysis.py`
To jest prostsza, lokalna warstwa analityczna do dashboardu.
Skrypt:

- czyta wszystkie lokalne CSV,
- stosuje te sama logike czyszczenia,
- liczy kilka podstawowych statystyk w Pandas,
- zapisuje gotowe pliki CSV do folderu `outputs/`.

Te wyniki sa potem odczytywane przez dashboard.

### `scripts/verify_month.py`
To jest skrypt walidacyjny.
Jego rola jest bardzo wazna, bo pozwala sprawdzic, czy Hadoop liczy to samo co Pandas.

On:

- bierze jeden miesiac danych,
- liczy statystyki referencyjne w Pandas,
- porownuje je z wynikiem z `mapreduce_results.tsv`,
- pokazuje, czy sa rozbieznosci.

To jest nasz argument, ze logika MapReduce jest poprawna.

### `app/dashboard.py`
To jest prosta wizualizacja w Streamlit.
Dashboard pokazuje:

- liczbe przejazdow per miesiac,
- sredni czas przejazdu per typ klienta,
- udzial typow rowerow,
- top stacje startowe.

To jest warstwa prezentacyjna, czyli koncowy, czytelny widok wynikow.

## Skad co czyta dane i gdzie co zapisuje
To jest bardzo praktyczna czesc, bo na konsultacjach czesto pada pytanie nie tylko "co robi skrypt", ale tez "na jakich danych pracuje i co produkuje".

### `scripts/push_to_hdfs.py`
- czyta archiwa z `data/raw/zip/`
- wysyla je do `HDFS` pod sciezki typu `/tripdata/raw/year=2024/month=01/...zip`

### `bigdata_project/hdfs_ops.py`
- nie czyta danych biznesowych bezposrednio
- obsluguje technicznie wysylke plikow do HDFS przez WebHDFS
- tworzy katalogi i uploaduje gotowe pliki

### `scripts/prepare_mapreduce_input.py`
- czyta ZIP-y z `HDFS/raw`
- rozpakowuje je roboczo i czysci
- przygotowuje lokalne pliki TSV w `data/processed/`
- wysyla te pliki do `HDFS` pod sciezki typu `/tripdata/processed_tmp/year=2024/month=01/...`

### `scripts/run_mapreduce.py`
- czyta dane z `HDFS`, konkretnie z `/tripdata/processed_tmp/...`
- uruchamia job Hadoop Streaming na tych danych
- wynik reducera najpierw jest w `HDFS` jako output joba
- potem skrypt sciaga wynik do lokalnego pliku `outputs/mapreduce_results.tsv`

### `hadoop/mapper.py`
- czyta wiersze TSV przekazane przez Hadoop ze zbioru w HDFS
- nie zapisuje plikow samodzielnie
- generuje czesciowe wyniki do dalszego laczenia

### `hadoop/reducer.py`
- czyta posortowane wyniki z mappera
- laczy rekordy dla tych samych kluczy
- zwraca wynik koncowy na standardowe wyjscie joba Hadoop

### `scripts/load_results_atlas.py`
- czyta lokalny plik `outputs/mapreduce_results.tsv`
- zamienia wynik na dokumenty
- zapisuje agregaty do `MongoDB Atlas`
- dodatkowo zapisuje podglad do `outputs/atlas_results_preview.json`

### `scripts/run_local_analysis.py`
- czyta wszystkie lokalne CSV z `data/raw/csv/`
- czysci je ta sama logika co w ETL
- liczy proste statystyki w Pandas
- zapisuje wyniki do:
  - `outputs/monthly_trips.csv`
  - `outputs/avg_duration_by_member_type.csv`
  - `outputs/bike_type_share.csv`
  - `outputs/top_start_stations.csv`
  - `outputs/analysis_summary.json`

### `scripts/verify_month.py`
- czyta lokalne CSV dla jednego miesiaca
- liczy wynik referencyjny w Pandas
- czyta lokalny wynik Hadoop z `outputs/mapreduce_results.tsv`
- porownuje obie wersje i pokazuje zgodnosc albo roznice

### `app/dashboard.py`
- nie czyta danych bezposrednio z HDFS
- nie czyta danych bezposrednio z MongoDB Atlas
- czyta lokalne pliki z folderu `outputs/`, przygotowane przez `scripts/run_local_analysis.py`
- na tej podstawie rysuje wykresy i tabele w Streamlit

Najprostsze zdanie do zapamietania:

"Dashboard czyta lokalne pliki wynikowe z folderu `outputs/`, a Atlas sluzy u nas do przechowywania wynikow analizy w chmurze."

## Prosty slowniczek pojec

### HDFS
`HDFS` to Hadoop Distributed File System.
Najprosciej mowiac jest to system plikow dla Hadoopa, czyli miejsce, w ktorym trzymamy dane do duzego przetwarzania.

Po co nam jest?

- bo wymaganie na `5.0` mowi, ze glowny zbior danych ma byc zapisany w HDFS
- bo Hadoop czyta dane wlasnie z HDFS
- bo dane sa tam ulozone tak, zeby dalo sie je przetwarzac w stylu big data

W naszym projekcie:

- glowny zbior w HDFS to archiwa ZIP w katalogu `raw`
- dodatkowo mamy tymczasowe wejscie `processed_tmp` tylko do uruchomienia MapReduce

### Hadoop
`Hadoop` to ekosystem do przechowywania i przetwarzania duzych danych.
W naszym projekcie najwazniejsze sa dwa elementy:

- `HDFS` - czyli przechowywanie danych
- `MapReduce` - czyli przetwarzanie danych

Czyli w uproszczeniu:

- HDFS przechowuje
- Hadoop przetwarza

### MapReduce
`MapReduce` to model przetwarzania danych na duza skale.
Dziala w dwoch glownych krokach:

- `map` - kazdy rekord jest analizowany osobno i zamieniany na pary klucz-wartosc
- `reduce` - rekordy z tym samym kluczem sa laczone i agregowane

W naszym projekcie:

- mapper rozbija przejazdy na metryki, na przyklad miesiac, typ klienta czy stacje
- reducer laczy te dane i liczy wyniki statystyczne

### Mapper
`Mapper` to pierwsza czesc MapReduce.
Jego zadanie polega na tym, zeby przeczytac pojedynczy rekord i powiedziec, do jakich analiz on nalezy.

Przyklad:

- jeden przejazd moze trafic jednoczesnie do statystyki miesiecznej,
- do statystyki po typie klienta,
- do statystyki po typie roweru,
- i do statystyki po stacji startowej.

### Reducer
`Reducer` to druga czesc MapReduce.
Jego zadanie to zebranie wszystkich rekordow tego samego typu i policzenie wyniku koncowego.

U nas reducer liczy:

- liczbe przejazdow,
- sume czasow,
- sredni czas,
- odchylenie standardowe.

### Hadoop Streaming
`Hadoop Streaming` to sposob uruchamiania MapReduce w jezykach innych niz Java.
U nas dzieki temu mozemy napisac `mapper.py` i `reducer.py` w Pythonie, a Hadoop potraktuje je jako elementy joba.

### NameNode
`NameNode` to glowny wezel HDFS.
On nie przechowuje calej tresci danych tak jak zwykly magazyn, tylko zarzadza systemem plikow.

Najprosciej mowiac:

- wie, jakie pliki sa w HDFS,
- wie, gdzie sa zapisane,
- zarzadza struktura katalogow i metadanymi.

Mozna powiedziec, ze NameNode jest "menedzerem" HDFS.

### DataNode
`DataNode` to wezel, ktory przechowuje dane.
Jesli NameNode wie, gdzie co jest, to DataNode faktycznie trzyma bloki plikow.

Najprosciej:

- NameNode zarzadza
- DataNode przechowuje

### WebHDFS
`WebHDFS` to HTTP API do komunikacji z HDFS.
U nas jest uzywane po to, zeby skrypt Pythonowy mogl wrzucac pliki do HDFS bez pisania wszystkiego przez linie komend Hadoop.

### Kontener NameNode i DataNode w projekcie
W Waszym projekcie oba te elementy sa uruchomione jako kontenery Docker:

- `bigdata-namenode`
- `bigdata-datanode`

Dzieki temu mozna lokalnie pokazac HDFS i Hadoop bez osobnego klastra na kilku maszynach.

## Jak moja czesc laczy sie z reszta projektu
Moja czesc bierze dane po czyszczeniu i robi z nimi dwie rzeczy:

### 1. Sciezka big data
- przygotowuje pliki do HDFS,
- wrzuca je do HDFS,
- uruchamia Hadoop Streaming,
- zapisuje wynik do MongoDB Atlas.

### 2. Sciezka prezentacyjna
- liczy proste lokalne statystyki,
- zapisuje je w `outputs/`,
- pokazuje je w dashboardzie Streamlit.

Czyli moja czesc laczy duze przetwarzanie z prezentacja wynikow.

## Jak moge to opowiedziec na konsultacji
Przykladowo moge powiedziec tak:

"Moja czesc projektu obejmuje warstwe big data i wyniki koncowe. Najpierw zapisujemy glowny zbior danych, czyli archiwa ZIP, do HDFS. Potem przygotowujemy osobne, tymczasowe wejscie TSV do Hadoop Streaming, bo na takim formacie najwygodniej uruchomic mapper i reducer w Pythonie. Wyniki joba sa eksportowane do lokalnego pliku, a nastepnie zapisywane jako agregaty w MongoDB Atlas. Dodatkowo przygotowujemy lokalne statystyki do dashboardu w Streamlit, zeby latwo pokazac wyniki analizy."

## O co moga zapytac i jak odpowiedziec

### Po co HDFS, skoro macie tez MongoDB?
Bo wymaganie na `5.0` mowi, ze glowny zbior danych ma byc przechowywany w HDFS. MongoDB sluzy u nas do przechowywania oczyszczonych danych lokalnie i wynikow agregacji.

### Po co Hadoop Streaming?
Bo projekt jest w Pythonie, a Hadoop Streaming pozwala uruchomic mapper i reducer napisany w Pythonie bez przepisywania logiki na Jave.

### Co zapisujecie do Atlas?
Nie glowny zbior przejazdow, tylko wyniki analiz: agregaty statystyczne, liczbe przejazdow, srednie czasy i inne metryki z MapReduce.

### Skad wiadomo, ze MapReduce dziala poprawnie?
Porownujemy wynik Hadoop z wynikiem referencyjnym z Pandas dla wybranego miesiaca przez `scripts/verify_month.py`.

### Po co lokalna analiza, skoro jest Hadoop?
Lokalna analiza sluzy glownie do szybkiej wizualizacji i dashboardu. Duze przetwarzanie i glowna analiza pod `5.0` odbywa sie przez HDFS i Hadoop Streaming.

### Czy dashboard bierze dane z Atlasa?
W obecnej wersji dashboard czyta lokalne pliki wynikowe z `outputs/`. Atlas sluzy do zapisania wynikow analizy w chmurze, zgodnie z wymaganiem projektu.

## Najwazniejsze zdanie do zapamietania
Moja rola polega na tym, zeby oczyszczone dane zapisac w HDFS, przetworzyc je przez Hadoop Streaming, zapisac agregaty w MongoDB Atlas i pokazac wyniki w czytelnej formie na dashboardzie.

## Krotkie streszczenie do powiedzenia
"W naszej czesci projektu odpowiadam za warstwe big data i prezentacje wynikow. Najpierw zapisujemy do HDFS glowny zbior danych w postaci archiwow ZIP. Potem przygotowujemy tymczasowe pliki TSV do Hadoop Streaming i na nich uruchamiamy mapper i reducer napisany w Pythonie, zeby policzyc najwazniejsze statystyki, na przyklad liczbe przejazdow, sredni czas czy rozklad po typie klienta i stacji. Wyniki joba zapisujemy do pliku, a potem do MongoDB Atlas jako agregaty. Dodatkowo przygotowujemy lokalne statystyki do dashboardu w Streamlit, zeby latwo pokazac wyniki analizy. Poprawnosc logiki Hadoop sprawdzamy przez porownanie wyniku z obliczeniami referencyjnymi w Pandas dla wybranego miesiaca."


### tests/test_manifest.py
Ten plik testuje logikę związaną z manifestem, czyli etapem scrapingu i wybierania plików.

Sprawdza 2 rzeczy:

1. parse_html_keys()
- bierze przykładowy fragment HTML
- sprawdza, czy funkcja wyciąga tylko linki do plików .zip
- ignoruje inne linki, np. notes.txt

2. filter_monthly_archives()
- bierze listę nazw plików z różnych lat
- sprawdza, czy funkcja poprawnie zostawia tylko pliki z wybranego roku, np. 2024

### tests/test_transform.py
Ten plik testuje czyszczenie danych w normalize_chunk().

Sprawdza 2 rzeczy:

1. Czy złe rekordy są odrzucane i dobre są wzbogacane
- tworzy 2 przykładowe przejazdy:
    - jeden poprawny
    - jeden błędny, gdzie koniec przejazdu jest wcześniej niż początek
- sprawdza, że zostaje tylko poprawny rekord
- sprawdza też, czy dobrze policzył się:
    - trip_duration_minutes
    - trip_year
    - source_file

2. Czy odpadają rekordy spoza NYC
- tworzy 1 rekord z poprawnymi współrzędnymi
- i 1 rekord z absurdalnymi współrzędnymi
- sprawdza, że zostaje tylko ten z Nowego Jorku