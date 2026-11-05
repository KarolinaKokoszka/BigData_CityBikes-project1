# Pytania do prowadzacej przed oddaniem projektu

## Po co ta lista
Projekt wyglada juz na bardzo bliski wymagan `5.0`, ale przed konsultacjami warto dopytac o kilka rzeczy, zeby nie okazalo sie, ze technicznie wszystko dziala, ale jakis formalny szczegol jest oceniany inaczej.

## Najwazniejsze pytania

### 1. Czy lokalne MongoDB moze byc bez TLS, jesli:
- jest uruchomione lokalnie w Dockerze,
- ma uwierzytelnienie login/haslo,
- a polaczenie do MongoDB Atlas jest szyfrowane i uwierzytelnione?

To jest chyba najwazniejsze pytanie w Waszym przypadku.
Obecnie:

- lokalny MongoDB ma logowanie,
- Atlas ma logowanie i TLS,
- ale lokalny MongoDB nie ma dodatkowego szyfrowania polaczenia.

Mozna to powiedziec prowadzacej prosto tak:

"Czy dla projektu na 5.0 wystarczy, ze lokalna baza MongoDB ma uwierzytelnienie, a szyfrowane polaczenie jest zapewnione dla MongoDB Atlas, czy lokalne MongoDB tez musi obslugiwac TLS?"

### 2. Czy glowny zbior danych moze byc przechowywany w HDFS po etapie czyszczenia?
W projekcie dane trafiaja do HDFS juz po normalizacji do TSV.
To zwykle jest sensowne, ale dobrze upewnic sie, czy to jest akceptowalne.

Mozna zapytac:

"Czy wymaganie o przechowywaniu glownego zbioru w HDFS jest spelnione, jesli do HDFS zapisujemy oczyszczone dane przygotowane do Hadoop Streaming, a nie surowe archiwa ZIP?"

### 3. Czy wystarczy, ze MongoDB Atlas przechowuje wyniki analiz i agregaty, a nie caly glowny zbior danych?
To powinno byc zgodne z trescia wymagan, ale warto to potwierdzic wprost.

Mozna zapytac:

"Czy na 5.0 wystarczy, ze w MongoDB Atlas zapisujemy wyniki analizy i agregaty z MapReduce, a glowny zbior danych przechowujemy w HDFS?"

### 4. Czy dashboard moze bazowac na lokalnie przygotowanych plikach wynikowych?
Obecnie dashboard czyta wyniki z `outputs/`, a nie bezposrednio z Atlasa.
Formalnie powinno byc OK, ale warto sprawdzic, czy prowadzaca nie oczekuje scislejszego polaczenia z MongoDB.

Mozna zapytac:

"Czy prosty dashboard moze korzystac z lokalnie przygotowanych wynikow CSV, jesli wyniki analizy sa rownolegle zapisane do MongoDB Atlas?"

### 5. Czy do walidacji Hadoop wystarczy porownanie jednego miesiaca z Pandas?
To jest bardzo sensowna metoda, ale dobrze upewnic sie, czy prowadzaca uzna to za wystarczajacy dowod poprawnosci.

Mozna zapytac:

"Czy jako potwierdzenie poprawnosci MapReduce wystarczy porownanie wynikow Hadoop z wynikiem referencyjnym z Pandas dla jednego wybranego miesiaca?"

### 6. Czy zakres jednego roku jest wystarczajacy, jesli przekracza 5 GB po rozpakowaniu?
Macie informacje, ze same dane za `2024` po wypakowaniu maja okolo `8 GB`, wiec warunek rozmiaru jest spelniony.
Warto jednak upewnic sie, czy nie trzeba koniecznie przetwarzac dwoch lat, tylko dlatego, ze byly rozwazane `2024-2025`.

Mozna zapytac:

"Jesli po wypakowaniu sam rok 2024 przekracza 5 GB, to czy taki zakres danych wystarczy na 5.0, czy oczekiwany jest koniecznie wiekszy przedzial?"

### 7. Czy lokalne MongoDB musi przechowywac caly zbior, czy moze przechowywac pelny lub reprezentatywny zakres?
To pytanie jest mniej krytyczne, ale moze sie przydac, jesli prowadzaca bedzie dopytywac o sens laczenia MongoDB i HDFS.

Mozna zapytac:

"Czy lokalna baza MongoDB powinna zawierac caly oczyszczony zbior, czy wystarczy, ze sluzy jako etap ETL i magazyn danych do testow oraz wstepnych analiz?"

### 8. Czy nasz sposob pozyskania listy plikow mozna uznac za web scraping?
To jest punkt, o ktory warto dopytac formalnie, bo u Was scraping nie polega na sciaganiu tresci artykulow czy rekordow ze strony, tylko na parsowaniu strony z linkami do plikow.

U Was to wyglada tak:

- skrypt pobiera strone lub listing z `tripdata`,
- odczytuje z HTML albo XML linki do archiwow `.zip`,
- filtruje tylko pliki miesieczne z interesujacego zakresu,
- buduje manifest, czyli liste plikow do dalszego pobrania,
- a same dane sa potem sciagane juz jako otwarte archiwa ZIP.

Czyli technicznie jest to scraping strony z linkami do danych, a nie reczne wpisanie adresow plikow.
Jednoczesnie prowadzaca moze uznac, ze to jest bardziej "parsowanie listingu i pobieranie otwartego zbioru" niz klasyczny scraping tresci strony.

Najlepiej zapytac to tak:

"W naszym projekcie web scraping polega na pobraniu strony lub listingu `tripdata`, sparsowaniu HTML albo XML, wyciagnieciu linkow do miesiecznych archiwow ZIP i zbudowaniu manifestu plikow do pobrania. Czy taki sposob mozemy potraktowac jako web scraping w rozumieniu wymagan projektu?"

## Najbardziej praktyczna wersja: o co zapytac na pewno
Jesli nie chcecie pytac o wszystko, to ja bym koniecznie zadal te 5 pytan:

1. Czy lokalne MongoDB bez TLS jest akceptowalne, jesli Atlas ma TLS i uwierzytelnienie?
2. Czy dane zapisane w HDFS po czyszczeniu nadal spelniaja wymog "glownego zbioru danych w HDFS"?
3. Czy Atlas moze przechowywac tylko agregaty i wyniki, a nie caly dataset?
4. Czy dashboard moze czytac lokalne wyniki, jesli Atlas tez zawiera wyniki analizy?
5. Czy parsowanie strony z linkami do archiwow i budowa manifestu mozna uznac za web scraping?

## Jak to ujac jednym zdaniem na konsultacji
Mozecie powiedziec na poczatku tak:

"Technicznie projekt juz dziala end-to-end i spelnia zalozenia ETL, HDFS, Hadoop Streaming, MongoDB Atlas i dashboardu. Chcialybysmy tylko doprecyzowac kilka formalnych kwestii do 5.0, glownie czy lokalne MongoDB musi miec TLS oraz czy Atlas moze przechowywac agregaty zamiast calego zbioru."

## Moja ocena ryzyka
Najwieksze ryzyko formalne widze w dwoch miejscach:

- lokalne MongoDB bez TLS
- to, czy prowadzaca uzna Wasz sposob parsowania listingu plikow za web scraping

Reszta wyglada bardzo sensownie pod wymagania `5.0`, bo:

- web scraping technicznie jest, ale dobrze go doprecyzowac formalnie,
- lokalny MongoDB jest,
- ponowne uruchomienie bez duplikacji jest,
- HDFS jest,
- Hadoop MapReduce jest,
- Atlas jest,
- wizualizacja jest,
- zakres danych przekracza 5 GB.
