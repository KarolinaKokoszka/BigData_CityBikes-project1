import math
import sys

"""
dla kazdej grupy liczone sa:
- liczba rekordow,
- suma czasu przejazdow,
- sredni czas,
- odchylenie standardowe
"""

def flush(key, n, s, q, final): 
    """wypisuje wynik dla jednego zakończonego klucza"""

    # pierwsze wywołanie, jeszcze nie ma żadnej grupy
    if key is None: 
        return
    
    if final: # podliczenie statystyk i wypisanie gotwego wiersza wyniku
        metric, dimension = key.split("|", 1)
        mean = s / n
        std = math.sqrt(max(0.0, q / n - mean * mean))
        print("{}\t{}\t{}\t{:.4f}\t{:.4f}\t{:.4f}".format(metric, dimension, n, s, mean, std))
    else: #wypisanie sum cząstkowych w formacie wejściowym, żeby kolejny reducer mógł je dalej łączyć
        print("{}\t{}\t{}\t{}".format(key, n, repr(s), repr(q)))


def main():
    final = len(sys.argv) > 1 and sys.argv[1] == "final"
    current = None # aktualny klucz
    n, s, q = 0, 0.0, 0.0 # liczniki dla bieżącego klucza

    for line in sys.stdin:
        p = line.rstrip("\n").split("\t")
        if len(p) != 4:
            continue

        # zmiana klucza oznacza koniec grupy
        if p[0] != current:
            flush(current, n, s, q, final) # zamyknięcie poprzedniej grupy
            current = p[0]
            n, s, q = 0, 0.0, 0.0 

        n += int(p[1])
        s += float(p[2])
        q += float(p[3])
    flush(current, n, s, q, final) # zamknięcie ostatniej grupy


if __name__ == "__main__":
    main()