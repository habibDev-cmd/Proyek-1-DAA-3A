"""Program utama Kasus E - Deduplikasi Log Server & Anomali Siber.

Pemakaian:  python main.py [iter|rec]
"""
import os
import sys

from log_anomaly import LogLoader, AnomalyPipeline

sys.setrecursionlimit(20000)

DATASET = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "dataset", "case5_server_access.txt")

PATTERNS = [
    "POST /healthcheck",
    "X11; Linux x86_64; rv:130.0",
    "340.213.18.221:2816",
]


def main():
    mode = "iter"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    lines = LogLoader(DATASET).load()
    pipeline = AnomalyPipeline(PATTERNS, recursive=(mode == "rec"))
    pipeline.run(lines)
    print(pipeline.render())


if __name__ == "__main__":
    main()
