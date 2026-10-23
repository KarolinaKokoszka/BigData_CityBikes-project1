# Sprawozdanie z projektu Big Data

## 1. Cel projektu
Projekt analizuje przejazdy Citi Bike z lat 2024-2025. Celem jest zbudowanie kompletnego pipeline'u do pobierania, czyszczenia, zapisu, przetwarzania i prezentacji danych z wykorzystaniem lokalnego MongoDB, MongoDB Atlas, HDFS oraz Hadoop Streaming.

## 2. Opis problemu i danych
- zrodlo danych: oficjalny zbior Citi Bike oraz indeks S3 `tripdata`,
- zakres: miesiace `2024-01` do `2025-12`,
- format: archiwa `.zip` zawierajace pliki `.csv`,
- glowne pola: `ride_id`, `rideable_type`, `started_at`, `ended_at`, `start_station_name`, `end_station_name`, `member_casual`.

## 3. Architektura rozwiazania
Wklej opis przeplywu danych:
- scraping listy plikow,
- pobieranie archiwow,
- staging i czyszczenie,
- zapis do MongoDB lokalnego,
- zapis przetworzonych plikow TSV do HDFS,
- analiza w Hadoop Streaming,
- zapis agregatow do MongoDB Atlas,
- wizualizacja w Streamlit.

## 4. Implementacja
Opisz:
- uzyte biblioteki Pythona,
- kontenery Docker,
- strukture katalogow,
- sposob unikania duplikatow przy restarcie importu,
- walidacje i czyszczenie danych.

## 5. Analizy statystyczne
Wstaw wyniki i interpretacje:
- liczba przejazdow per miesiac,
- sredni czas przejazdu per typ klienta,
- udzial typow rowerow,
- top stacje startowe,
- rozklad przejazdow per dzien tygodnia.

## 6. Hadoop i HDFS
Opisz:
- format danych wrzucanych do HDFS,
- logike `mapper.py` i `reducer.py`,
- sposob uruchamiania Hadoop Streaming,
- gdzie trafiaja wyniki.

## 7. Bezpieczenstwo i dostep do baz
Opisz:
- logowanie do lokalnego MongoDB,
- polaczenie TLS do MongoDB Atlas przez `mongodb+srv`,
- przechowywanie danych dostepowych w `.env`.

## 8. Instrukcja uruchomienia
Wstaw kroki z README:
1. instalacja zaleznosci,
2. start kontenerow,
3. wygenerowanie manifestu,
4. pobranie i staging,
5. import do MongoDB lokalnego,
6. export TSV do HDFS,
7. uruchomienie MapReduce,
8. zapis wynikow do Atlas,
9. start dashboardu.

## 9. Wnioski
Podsumuj:
- co udalo sie zrealizowac,
- jakie sa najwazniejsze trendy w danych,
- jakie sa ograniczenia rozwiazania,
- jak mozna projekt rozwinac dalej.
