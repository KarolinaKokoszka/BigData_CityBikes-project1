import sys
from collections import defaultdict

"""
tworzone klucze:
- liczba przejazdow per miesiac,
- sredni czas przejazdu per typ klienta,
- liczba przejazdow per typ roweru,
- liczba przejazdow per dzien tygodnia,
- liczba przejazdow per stacja startowa,
- liczba przejazdow per godzina i typ klienta
"""

def main():
    acc = defaultdict(lambda: [0, 0.0, 0.0])  #słownik: klucz "metryka|wymiar" -> [liczba przejazdów, suma czasów, suma kwadratów czasów]

    for line in sys.stdin:
        f = line.rstrip("\n").split("\t")
        # pominięcie linii o złej liczbie pól oraz ewentualny nagłówek
        if len(f) != 9 or f[0] == "trip_year":
            continue
        # czas przejazdu musi być liczbą, inaczej pominięcie rekordu
        try:
            d = float(f[8])
        except ValueError:
            continue

        year, month, dow, hour, member, bike, start_station, _end, _dur = f
        # jeden przejazd -> 6 różnych statystyk jednocześnie
        keys = [
            ("rides_by_month", "{}-{}".format(year, month.zfill(2))),
            ("duration_by_member_type", member),
            ("rides_by_bike_type", bike),
            ("rides_by_day_of_week", dow),
            ("rides_by_hour", "{}|{}".format(hour.zfill(2), member)),
            ("rides_by_start_station", start_station),
        ]

        # aktualizacja słownika dla każdego klucza
        for metric, dimension in keys:
            a = acc["{}|{}".format(metric, dimension)]
            a[0] += 1 # liczba przejazdów
            a[1] += d # suma czasów
            a[2] += d * d # suma kwadratów czasów

    # wypisanie po jednej linii na klucz 
    for key, a in acc.items():
        print("{}\t{}\t{}\t{}".format(key, a[0], repr(a[1]), repr(a[2])))


if __name__ == "__main__":
    main()