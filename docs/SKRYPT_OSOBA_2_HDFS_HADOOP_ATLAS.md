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

## Jak wyglada przeplyw danych w mojej czesci
Kolejnosc jest taka:

1. `scripts/push_to_hdfs.py` bierze lokalne CSV i przygotowuje pliki TSV pod Hadoop.
2. `bigdata_project/hdfs_ops.py` wrzuca te pliki do HDFS przez WebHDFS.
3. `docker-compose.yml` uruchamia lokalne srodowisko z NameNode, DataNode i MongoDB.
4. `docker/hadoop-python/Dockerfile` dodaje `python3` do kontenerow Hadoop, zeby dzialal Streaming w Pythonie.
5. `scripts/run_mapreduce.py` uruchamia job Hadoop Streaming.
6. `hadoop/mapper.py` zamienia kazdy przejazd na pary klucz-wartosc do analiz.
7. `hadoop/reducer.py` laczy wyniki i liczy agregaty koncowe.
8. `scripts/load_results_atlas.py` zapisuje wyniki do MongoDB Atlas.
9. `scripts/run_local_analysis.py` tworzy proste lokalne statystyki do dashboardu.
10. `scripts/verify_month.py` porownuje wynik Hadoop z wynikiem referencyjnym z Pandas dla jednego miesiaca.
11. `app/dashboard.py` pokazuje wykresy i tabele.

## Co mowie o kazdym pliku

### `scripts/push_to_hdfs.py`
Ten skrypt przygotowuje dane pod Hadoop.
On:

- czyta surowe lokalne CSV,
- przepuszcza je przez te sama logike czyszczenia co import do MongoDB,
- wybiera tylko kolumny potrzebne do analiz,
- zapisuje wynik jako pliki TSV,
- wrzuca te pliki do HDFS.

Wazne jest to, ze dane do HDFS nie sa surowe, tylko juz oczyszczone i ujednolicone.

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
- uruchamia job na danych z HDFS,
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

"Moja czesc projektu obejmuje warstwe big data i wyniki koncowe. Najpierw przygotowujemy oczyszczone dane do formatu TSV i zapisujemy je w HDFS. Potem uruchamiamy Hadoop Streaming z mapperem i reducerem napisanym w Pythonie. Wyniki joba sa eksportowane do lokalnego pliku, a nastepnie zapisywane jako agregaty w MongoDB Atlas. Dodatkowo przygotowujemy lokalne statystyki do dashboardu w Streamlit, zeby latwo pokazac wyniki analizy."

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
"W naszej czesci projektu odpowiadam za warstwe big data i prezentacje wynikow. Najpierw przygotowujemy oczyszczone dane do formatu TSV i zapisujemy je w HDFS. Potem uruchamiamy Hadoop Streaming z mapperem i reducerem napisanym w Pythonie, zeby policzyc najwazniejsze statystyki, na przyklad liczbe przejazdow, sredni czas czy rozklad po typie klienta i stacji. Wyniki joba zapisujemy do pliku, a potem do MongoDB Atlas jako agregaty. Dodatkowo przygotowujemy lokalne statystyki do dashboardu w Streamlit, zeby latwo pokazac wyniki analizy. Poprawnosc logiki Hadoop sprawdzamy przez porownanie wyniku z obliczeniami referencyjnymi w Pandas dla wybranego miesiaca."
