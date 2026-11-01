"""Simulasi dan eksperimen (butir 12 dan 13): waktu, memori, jumlah operasi.

Jalankan:  python experiment.py   (hasil juga disimpan ke results.json)
"""
import json
import os
import sys
import time
import tracemalloc

from log_anomaly import (LogLoader, AnomalyPipeline, OperationCounter,
                         KMPMatcher, MergeSorter, AnomalyResult)

sys.setrecursionlimit(20000)
HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset", "case5_server_access.txt")
PATTERNS = ["POST /healthcheck", "X11; Linux x86_64; rv:130.0", "340.213.18.221:2816"]


class DepthMatcher(KMPMatcher):
    """KMPMatcher yang mencatat kedalaman rekursi maksimum."""
    depth = 0
    max_depth = 0

    def _search_rec(self, text, i, j):
        DepthMatcher.depth += 1
        if DepthMatcher.depth > DepthMatcher.max_depth:
            DepthMatcher.max_depth = DepthMatcher.depth
        try:
            return KMPMatcher._search_rec(self, text, i, j)
        finally:
            DepthMatcher.depth -= 1


class DepthSorter(MergeSorter):
    depth = 0
    max_depth = 0

    def sort_recursive(self, items):
        DepthSorter.depth += 1
        if DepthSorter.depth > DepthSorter.max_depth:
            DepthSorter.max_depth = DepthSorter.depth
        try:
            return MergeSorter.sort_recursive(self, items)
        finally:
            DepthSorter.depth -= 1


def measure(lines, patterns, recursive, repeats=3):
    """Mengembalikan (waktu rata-rata detik, operasi karakter, puncak memori KB)."""
    total = 0.0
    ops = 0
    for _ in range(repeats):
        p = AnomalyPipeline(patterns, recursive)
        t0 = time.perf_counter()
        p.run(lines)
        total += time.perf_counter() - t0
        ops = p.counter.count
    tracemalloc.start()
    p = AnomalyPipeline(patterns, recursive)
    p.run(lines)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return total / repeats, ops, peak / 1024.0


def scaling(base):
    rows = []
    sizes = [500, 1000, 2000, 3459, 6918, 13836]
    for n in sizes:
        lines = []
        for k in range(n):
            lines.append(base[k % len(base)])
        chars = 0
        for ln in lines:
            chars += len(ln)
        ti, oi, mi = measure(lines, PATTERNS, False)
        tr, orr, mr = measure(lines, PATTERNS, True)
        rows.append({"n_lines": n, "chars": chars,
                     "iter_time_s": ti, "iter_ops": oi, "iter_mem_kb": mi,
                     "rec_time_s": tr, "rec_ops": orr, "rec_mem_kb": mr})
        print("n=%6d chars=%8d | iter %.3fs ops=%8d mem=%7.1fKB | rec %.3fs ops=%8d mem=%7.1fKB"
              % (n, chars, ti, oi, mi, tr, orr, mr))
    return rows


def kmp_best_worst():
    n_lines, width, m = 3459, 295, 20
    pat = "a" + "b" * (m - 1)
    worst_pat = "a" * (m - 1) + "b"            # hampir cocok di setiap posisi
    scenarios = (
        # terbaik: pola cocok di awal setiap baris -> berhenti dini setelah m perbandingan
        ("terbaik", pat, [pat + "b" * (width - m)] * n_lines),
        # pembanding: tidak ada kecocokan, mismatch di karakter pertama pola (1 per karakter)
        ("tanpa_kecocokan", pat, ["b" * width] * n_lines),
        # terburuk: teks "aaaa..." dan pola "aaa...ab"
        ("terburuk", worst_pat, ["a" * width] * n_lines),
    )
    out = {}
    for name, pt, lines in scenarios:
        N = n_lines * width
        res = {"N_karakter": N, "m": m, "n_lines": n_lines}
        for kind in ("iter", "rec"):
            p = AnomalyPipeline([pt], kind == "rec")
            t0 = time.perf_counter()
            p.run(lines)
            dt = time.perf_counter() - t0
            res[kind + "_ops"] = p.counter.count
            res[kind + "_time_s"] = dt
        res["rasio_ops_per_N"] = res["iter_ops"] / float(N)
        out[name] = res
        print("KMP %-16s N=%d ops_iter=%d ops_rec=%d rasio=%.3f  t_iter=%.3fs t_rec=%.3fs"
              % (name, N, res["iter_ops"], res["rec_ops"], res["rasio_ops_per_N"],
                 res["iter_time_s"], res["rec_time_s"]))
    # kedalaman rekursi terburuk untuk satu baris
    DepthMatcher.depth = 0
    DepthMatcher.max_depth = 0
    c = OperationCounter()
    mm = DepthMatcher(worst_pat, c)
    mm.build_lps_iterative()
    mm.search_recursive("a" * width)
    out["kedalaman_rekursi_terburuk"] = DepthMatcher.max_depth
    out["lebar_baris"] = width
    print("Kedalaman rekursi maksimum KMP (baris %d karakter, kasus terburuk): %d" % (width, DepthMatcher.max_depth))
    return out


def interleaved_worst(values):
    """Susun input sehingga setiap merge selang-seling (n-1 perbandingan)."""
    if len(values) <= 1:
        return values[:]
    evens = []
    odds = []
    for t in range(len(values)):
        if t % 2 == 0:
            evens.append(values[t])
        else:
            odds.append(values[t])
    return interleaved_worst(evens) + interleaved_worst(odds)


def sort_best_worst():
    out = {}
    for k in (1024, 4096):
        row = {}
        for name in ("terbaik (sudah terurut)", "terburuk (selang-seling)"):
            ranks = []
            for t in range(k):
                ranks.append(t + 1)
            if name.startswith("terburuk"):
                ranks = interleaved_worst(ranks)
            items = []
            for t in range(k):
                r = AnomalyResult("p%d" % t, t)
                r.frequency = ranks[t]
                items.append(r)
            res = {}
            for kind in ("iter", "rec"):
                s = MergeSorter() if kind == "iter" else DepthSorter()
                t0 = time.perf_counter()
                _ = s.sort_iterative(items) if kind == "iter" else s.sort_recursive(items)
                res[kind + "_cmp"] = s.comparisons
                res[kind + "_time_s"] = time.perf_counter() - t0
            tracemalloc.start()
            MergeSorter().sort_iterative(items)
            res["iter_mem_kb"] = tracemalloc.get_traced_memory()[1] / 1024.0
            tracemalloc.stop()
            DepthSorter.depth = 0
            DepthSorter.max_depth = 0
            tracemalloc.start()
            DepthSorter().sort_recursive(items)
            res["rec_mem_kb"] = tracemalloc.get_traced_memory()[1] / 1024.0
            tracemalloc.stop()
            res["rec_max_depth"] = DepthSorter.max_depth
            row[name] = res
            print("Sort k=%d %-26s cmp iter=%d rec=%d  mem iter=%.1fKB rec=%.1fKB  depth_rec=%d"
                  % (k, name, res["iter_cmp"], res["rec_cmp"], res["iter_mem_kb"],
                     res["rec_mem_kb"], res["rec_max_depth"]))
        out[str(k)] = row
    return out


def dataset_depth(base):
    DepthMatcher.depth = 0
    DepthMatcher.max_depth = 0
    c = OperationCounter()
    mm = DepthMatcher("POST /healthcheck", c)
    mm.build_lps_iterative()
    longest = 0
    for ln in base:
        mm.search_recursive(ln)
        if len(ln) > longest:
            longest = len(ln)
    print("Dataset asli: kedalaman rekursi maksimum KMP = %d (baris terpanjang %d karakter)"
          % (DepthMatcher.max_depth, longest))
    return {"max_depth": DepthMatcher.max_depth, "longest_line": longest}


def main():
    loader = LogLoader(DATASET)
    base = loader.load()
    print("Dataset: %d baris, %d byte" % (len(base), loader.size_bytes))
    result = {"dataset_lines": len(base), "dataset_bytes": loader.size_bytes}
    print("\n== Skala input ==")
    result["scaling"] = scaling(base)
    print("\n== KMP terbaik/terburuk ==")
    result["kmp"] = kmp_best_worst()
    print("\n== Merge Sort terbaik/terburuk ==")
    result["sort"] = sort_best_worst()
    print("\n== Kedalaman rekursi pada dataset ==")
    result["depth_dataset"] = dataset_depth(base)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
