import argparse
import re
import subprocess
import sys
import time

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS

CONTAINER = "bigdata-namenode"
STREAMING_JAR = "/opt/hadoop-3.2.1/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar"
COUNTERS = ("Map input records", "Map output records", "Reduce input groups", "Reduce output records")


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Hadoop Streaming job and export results.")
    parser.add_argument("--subdir", help="Only part of the data, e.g. year=2024/month=01")
    parser.add_argument("--output", default="/tripdata/output_stats", help="HDFS output directory")
    return parser.parse_args()


def docker_exec(command):
    return subprocess.run(
        ["docker", "exec", CONTAINER, "bash", "-c", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def main():
    args = parse_args()
    hadoop_dir = SETTINGS.project_root / "hadoop"
    SETTINGS.outputs_dir.mkdir(parents=True, exist_ok=True)

    # skopiowanie mapper.py i reducer.py do kontenera NameNode
    for name in ("mapper.py", "reducer.py"):
        subprocess.run(
            ["docker", "cp", str(hadoop_dir / name), "{}:/tmp/{}".format(CONTAINER, name)],
            check=True,
        )

    if docker_exec("python3 --version").returncode != 0:
        sys.exit("No python3 in the namenode container. Install it first (see README).")

    input_path = SETTINGS.hdfs_processed_dir + ("/" + args.subdir if args.subdir else "")
    # komenda dla Hadoop Streaming
    command = (
        "mkdir -p /tmp/mrwork && cd /tmp/mrwork && rm -f mapper.py reducer.py; "
        "hdfs dfs -rm -r -f {out}; hadoop jar {jar} "
        "-D mapreduce.input.fileinputformat.input.dir.recursive=true "
        "-files /tmp/mapper.py,/tmp/reducer.py "
        "-mapper 'python3 mapper.py' -combiner 'python3 reducer.py' "
        "-reducer 'python3 reducer.py final' -input {inp} -output {out}"
    ).format(out=args.output, jar=STREAMING_JAR, inp=input_path)

    log_path = SETTINGS.outputs_dir / "mapreduce_job.log"
    counters = {}
    start = time.time()
    # uruchomienie joba 
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            ["docker", "exec", CONTAINER, "bash", "-c", command],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )

        for line in proc.stdout:
            log.write(line)
            if "mapreduce.Job:" in line and " map " in line:
                print(line.strip())
            for name in COUNTERS:
                match = re.search(re.escape(name) + r"=(\d+)", line)
                if match:
                    counters.setdefault(name, []).append(int(match.group(1)))
        proc.wait()
    elapsed = time.time() - start

    if proc.returncode != 0:
        sys.exit("Job failed, see {}".format(log_path))

    print("Job time: {:.0f} s ({:.1f} min)".format(elapsed, elapsed / 60))
    for name in COUNTERS:
        if name in counters:
            print("{}: {}".format(name, counters[name][-1]))

    # scalenie plików wynikowych z HDFS w jeden plik w kontenerze
    docker_exec("hdfs dfs -getmerge {} /tmp/mapreduce_results.tsv".format(args.output))

    #pobieranie wynik z HDFS do lokalnego pliku outputs/mapreduce_results.tsv
    target = SETTINGS.outputs_dir / "mapreduce_results.tsv"
    subprocess.run(
        ["docker", "cp", "{}:/tmp/mapreduce_results.tsv".format(CONTAINER), str(target)],
        check=True,
    )
    print("Results exported to", target)


if __name__ == "__main__":
    main()