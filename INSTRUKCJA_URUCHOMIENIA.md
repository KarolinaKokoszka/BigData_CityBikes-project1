# Szybka instrukcja uruchomienia

## 1. Wymagania
- Python
- Docker Desktop

## 2. Przygotowanie
W folderze projektu uruchom:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

W pliku `.env` ustaw:

```env
HDFS_USER=root
```

## 3. Start baz i HDFS

```powershell
docker compose up -d --build
```

## 4. Test na 1 miesiacu

```powershell
python scripts/scrape_tripdata.py
python scripts/download_and_stage.py --year 2024 --month 1 --limit 1
python scripts/load_local_mongo.py --year 2024 --month 1 --limit 1
python scripts/run_local_analysis.py
python scripts/push_to_hdfs.py --year 2024 --month 1 --limit 1
```

## 5. Sprawdzenie HDFS

```powershell
docker exec -it bigdata-namenode hdfs dfs -ls /tripdata/processed/year=2024/month=01
```

## 6. Uwaga
MongoDB Atlas nie jest potrzebny do pierwszych testow lokalnych.
