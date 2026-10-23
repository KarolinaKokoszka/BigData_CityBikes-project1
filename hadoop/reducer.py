import math
import sys


def flush(key, n, s, q, final):
    if key is None:
        return
    if final:
        metric, dimension = key.split("|", 1)
        mean = s / n
        std = math.sqrt(max(0.0, q / n - mean * mean))
        print("{}\t{}\t{}\t{:.4f}\t{:.4f}\t{:.4f}".format(metric, dimension, n, s, mean, std))
    else:
        print("{}\t{}\t{}\t{}".format(key, n, repr(s), repr(q)))


def main():
    final = len(sys.argv) > 1 and sys.argv[1] == "final"
    current = None
    n, s, q = 0, 0.0, 0.0
    for line in sys.stdin:
        p = line.rstrip("\n").split("\t")
        if len(p) != 4:
            continue
        if p[0] != current:
            flush(current, n, s, q, final)
            current = p[0]
            n, s, q = 0, 0.0, 0.0
        n += int(p[1])
        s += float(p[2])
        q += float(p[3])
    flush(current, n, s, q, final)


if __name__ == "__main__":
    main()