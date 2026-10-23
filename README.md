# Big Data Project 1: Citi Bike 2024-2025

Projekt realizuje kompletny pipeline dla danych Citi Bike z lat 2024-2025:
- pobieranie listy miesiecznych archiwow ze zrodla `tripdata`,
- staging i czyszczenie danych w Pythonie,
- idempotentny import do lokalnego MongoDB,
- przygotowanie danych TSV do HDFS,
- analize statystyczna w Hadoop Streaming,
- zapis wynikow do MongoDB Atlas,
- prezentacje wynikow w `Streamlit`.

## Zakres danych
- lata: `2024, 2025`,
- format wejsciowy: oficjalne archiwa `.zip` z plikami `.csv`,
- glowny zakres plikow: `202401-citibike-tripdata.zip` do `202512-citibike-tripdata.zip`.

## Struktura projektu
- `bigdata_project/` - wspolna logika ETL, MongoDB i HDFS,
- `scripts/` - skrypty uruchomieniowe kolejnych etapow,
- `hadoop/` - mapper i reducer dla Hadoop Streaming,
- `app/` - prosty dashboard `Streamlit`,
- `docs/` - szkic sprawozdania,
- `tests/` - testy jednostkowe.

## Wymagania
1. Python `3.11+`
2. Docker Desktop
3. Konto `MongoDB Atlas` dla bazy chmurowej

## Instalacja
```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Po skopiowaniu pliku `.env` upewnijcie sie, ze dla dolaczonego `docker-compose.yml` ustawione jest:
```env
HDFS_USER=root
```

## Start uslug
```powershell
docker compose up -d
```

To uruchomi:
- lokalne `MongoDB`,
- `HDFS NameNode`,
- `HDFS DataNode`.

## Kolejnosc uruchamiania pipeline
### 1. Zbudowanie manifestu
```powershell
python scripts/scrape_tripdata.py
```

Mozecie tez zawezic zakres:
```powershell
python scripts/scrape_tripdata.py --years 2024
```

### 2. Pobranie i rozpakowanie danych
```powershell
python scripts/download_and_stage.py
```

Do szybkiego testu jednego miesiaca:
```powershell
python scripts/download_and_stage.py --year 2024 --month 1 --limit 1
```

### 3. Import do lokalnego MongoDB
```powershell
python scripts/load_local_mongo.py
```

Analogicznie mozna ladowac tylko wycinek:
```powershell
python scripts/load_local_mongo.py --year 2024 --month 1 --limit 1
```

Import jest idempotentny:
- kolekcja `imported_files` przechowuje status importu per archiwum,
- rekordy w `tripdata_cleaned_local` maja `_id = ride_id::source_file`,
- ponowne uruchomienie nie powinno duplikowac danych.

### 4. Przygotowanie danych pod Hadoop i upload do HDFS
```powershell
python scripts/push_to_hdfs.py
```

Do testu:
```powershell
python scripts/push_to_hdfs.py --year 2024 --month 1 --limit 1
```

Skrypt:
- czyta lokalne CSV,
- normalizuje pola,
- zapisuje TSV do `data/processed/`,
- wrzuca wynik do `HDFS` przez `WebHDFS`.

### 5. Hadoop Streaming
Przykladowe uruchomienie nalezy wykonac w kontenerze z Hadoop CLI lub w srodowisku z dostepem do `hadoop`:

```bash
hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /tripdata/processed \
  -output /tripdata/output_stats \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -file hadoop/mapper.py \
  -file hadoop/reducer.py
```

Po zakonczeniu zapisz wynik do lokalnego pliku `outputs/mapreduce_results.tsv`.

### 6. Zapis wynikow do MongoDB Atlas
```powershell
python scripts/load_results_atlas.py
```

### 7. Wizualizacja
```powershell
streamlit run app/dashboard.py
```

## Proponowany podzial pracy
### Osoba A
- `scrape_tripdata.py`
- `download_and_stage.py`
- `load_local_mongo.py`
- `push_to_hdfs.py`
- Docker i uruchomienie baz

### Osoba B
- `mapper.py`
- `reducer.py`
- `load_results_atlas.py`
- `run_local_analysis.py`
- `app/dashboard.py`
- sprawozdanie i interpretacja wynikow

## Analizy gotowe w repo
Skrypt `scripts/run_local_analysis.py` zapisuje:
- liczbe przejazdow per miesiac,
- sredni czas przejazdu per typ klienta,
- udzial typow rowerow,
- top 10 stacji startowych,
- pliki CSV i podsumowanie JSON do folderu `outputs/`.

## Testy
```powershell
python -m pytest
```

## Zrodla
- [Citi Bike System Data](https://citibikenyc.com/system-data)
- [S3 tripdata index](https://s3.amazonaws.com/tripdata/index.html)
