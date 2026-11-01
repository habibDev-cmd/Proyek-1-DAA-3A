"""Pengujian correctness & termination (butir 4 dan 5) serta simulasi (butir 12).

Pembanding (oracle) ditulis manual: tanpa in, find, re, sorted, Counter.
Jalankan:  python tests.py
"""
import os
import random
import sys

from log_anomaly import (OperationCounter, KMPMatcher, LogScanner,
                         MergeSorter, LogLoader, AnomalyResult)

sys.setrecursionlimit(20000)
HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset", "case5_server_access.txt")
RESULTS = []


def record(proses, tahap, ok, detail):
    RESULTS.append((proses, tahap, ok, detail))
    print("[%s] %-34s %-15s %s" % ("SESUAI" if ok else "GAGAL ", proses, tahap, detail))


# ----------------------------- oracle manual -----------------------------
def naive_find(text, pat):
    for s in range(len(text) - len(pat) + 1):
        k = 0
        while k < len(pat) and text[s + k] == pat[k]:
            k += 1
        if k == len(pat):
            return s
    return -1


def naive_lps(p):
    out = []
    for i in range(len(p)):
        best = 0
        for L in range(1, i + 1):
            if p[0:L] == p[i + 1 - L:i + 1]:
                best = L
        out.append(best)
    return out


def rand_str(rng, alphabet, n):
    s = ""
    for _ in range(n):
        s += alphabet[rng.randrange(len(alphabet))]
    return s


def is_ordered(items, sorter):
    for k in range(len(items) - 1):
        if not sorter.less_equal(items[k], items[k + 1]):
            return False
    return True


# ----------------------------- pengukur penurunan (termination) -----------
def lps_measure_trace(p):
    """M = 2(m-i) + length harus bilangan bulat >= 0 dan menurun tegas tiap iterasi."""
    m = len(p)
    lps = [0] * m
    length, i = 0, 1
    prev = 2 * (m - i) + length
    steps, ok = 0, True
    while i < m:
        if p[i] == p[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length - 1]
        else:
            i += 1
        cur = 2 * (m - i) + length
        if cur < 0 or cur >= prev:
            ok = False
        prev = cur
        steps += 1
    return ok, steps


def search_measure_trace(text, p):
    """M = (n-i) + (n-s), s = i-j, harus >= 0 dan menurun tegas tiap iterasi."""
    lps = naive_lps(p)
    n, m = len(text), len(p)
    i = j = 0
    prev = (n - i) + (n - (i - j))
    steps, ok = 0, True
    while i < n:
        if text[i] == p[j]:
            i += 1
            j += 1
            if j == m:
                steps += 1
                cur = (n - i) + (n - (i - j))
                if cur < 0 or cur >= prev:
                    ok = False
                break
        elif j != 0:
            j = lps[j - 1]
        else:
            i += 1
        cur = (n - i) + (n - (i - j))
        if cur < 0 or cur >= prev:
            ok = False
        prev = cur
        steps += 1
    return ok, steps


# =============================== PROSES 1: LPS ===============================
def test_lps():
    P = "Proses 1 - Tabel LPS (KMP)"
    c = OperationCounter()
    for kind in ("iter", "rec"):
        m = KMPMatcher("ABABCABAB", c)
        got = m.build_lps_iterative() if kind == "iter" else m.build_lps_recursive()
        want = [0, 0, 1, 2, 0, 1, 2, 3, 4]
        record(P + " [" + kind + "]", "Initialization", got[0] == 0,
               "lps[0]=%d (harapan 0)" % got[0])
        record(P + " [" + kind + "]", "Maintenance", got == want,
               "ABABCABAB -> %s" % got)
        rng = random.Random(1)
        bad = 0
        for _ in range(300):
            pat = rand_str(rng, "ab", rng.randrange(1, 14))
            mm = KMPMatcher(pat, c)
            res = mm.build_lps_iterative() if kind == "iter" else mm.build_lps_recursive()
            if res != naive_lps(pat):
                bad += 1
        record(P + " [" + kind + "]", "Termination", bad == 0 and len(got) == 9,
               "300 pola acak = definisi LPS, selisih=%d, panjang tabel=m" % bad)


# =============================== PROSES 2: Search ============================
def test_search():
    P = "Proses 2 - Pencarian KMP"
    c = OperationCounter()
    for kind in ("iter", "rec"):
        def run(text, pat):
            mm = KMPMatcher(pat, c)
            mm.build_lps_iterative()
            return mm.search_iterative(text) if kind == "iter" else mm.search_recursive(text)
        ok_init = run("", "AB") == -1 and run("ABC", "ABC") == 0
        record(P + " [" + kind + "]", "Initialization", ok_init,
               "teks kosong -> -1; teks=pola -> 0")
        rng = random.Random(2)
        bad = 0
        for _ in range(500):
            pat = rand_str(rng, "ab", rng.randrange(1, 6))
            txt = rand_str(rng, "ab", rng.randrange(0, 30))
            if run(txt, pat) != naive_find(txt, pat):
                bad += 1
        record(P + " [" + kind + "]", "Maintenance", bad == 0,
               "500 kasus acak = brute-force manual, selisih=%d" % bad)
        c.reset()
        mm = KMPMatcher("XYZ", c)
        mm.build_lps_iterative()
        c.reset()
        txt = "ABCDEFGHIJ"
        r = mm.search_iterative(txt) if kind == "iter" else mm.search_recursive(txt)
        record(P + " [" + kind + "]", "Termination", r == -1 and c.count <= 2 * len(txt),
               "tidak ada -> -1 setelah %d perbandingan (<= 2n=%d)" % (c.count, 2 * len(txt)))


# =============================== PROSES 3: Scan ==============================
def test_scan():
    P = "Proses 3 - Pemindaian log"
    for kind in ("iter", "rec"):
        rec = (kind == "rec")
        c = OperationCounter()
        sc = LogScanner(["ab"], c, rec)
        ok_init = sc.results[0].frequency == 0 and sc.results[0].first_line == -1
        sc.scan([])
        ok_init = ok_init and sc.results[0].frequency == 0
        record(P + " [" + kind + "]", "Initialization", ok_init,
               "sebelum/sesudah log kosong: frekuensi=0, indeks=-1")
        rng = random.Random(3)
        lines = []
        for _ in range(200):
            lines.append(rand_str(rng, "abc", rng.randrange(0, 12)))
        pats = ["ab", "ca", "bbb", "zz"]
        c = OperationCounter()
        sc = LogScanner(pats, c, rec)
        sc.scan(lines)
        bad = 0
        for k in range(len(pats)):
            cnt, first = 0, -1
            for idx in range(len(lines)):
                if naive_find(lines[idx], pats[k]) != -1:
                    cnt += 1
                    if first == -1:
                        first = idx + 1
            if cnt != sc.results[k].frequency or first != sc.results[k].first_line:
                bad += 1
        record(P + " [" + kind + "]", "Maintenance", bad == 0,
               "200 baris x 4 pola = penghitungan manual, pola berbeda=%d" % bad)
        real = LogLoader(DATASET).load()
        c = OperationCounter()
        pats2 = ["POST /healthcheck", "X11; Linux x86_64; rv:130.0", "340.213.18.221:2816"]
        sc = LogScanner(pats2, c, rec)
        sc.scan(real)
        got = [(r.frequency, r.first_line) for r in sc.results]
        want = [(24, 350), (299, 15), (0, -1)]       # acuan: grep -cF / grep -nF -m1
        record(P + " [" + kind + "]", "Termination", got == want and len(real) == 3459,
               "3459 baris selesai; (frek,indeks)=%s" % got)


# =============================== PROSES 4: Merge Sort ========================
def make_items(freqs):
    items = []
    for k in range(len(freqs)):
        r = AnomalyResult("p%d" % k, k)
        r.frequency = freqs[k]
        items.append(r)
    return items


def test_sort():
    P = "Proses 4 - Merge Sort"
    for kind in ("iter", "rec"):
        s = MergeSorter()
        fn = s.sort_iterative if kind == "iter" else s.sort_recursive
        ok_init = fn([]) == [] and len(fn(make_items([5]))) == 1
        record(P + " [" + kind + "]", "Initialization", ok_init,
               "daftar kosong dan 1 elemen dikembalikan apa adanya")
        rng = random.Random(4)
        bad = 0
        for _ in range(300):
            n = rng.randrange(0, 40)
            freqs = []
            for _ in range(n):
                freqs.append(rng.randrange(0, 6))
            items = make_items(freqs)
            out = fn(items)
            if len(out) != n or not is_ordered(out, s):
                bad += 1
                continue
            seen = [0] * n                       # semua elemen asli tepat satu kali
            for it in out:
                seen[it.order] += 1
            for v in seen:
                if v != 1:
                    bad += 1
                    break
        record(P + " [" + kind + "]", "Maintenance", bad == 0,
               "300 daftar acak: terurut (0 di akhir), permutasi lengkap, gagal=%d" % bad)
        out = fn(make_items([231, 119, 0, 7, 0, 119]))
        got = [(o.frequency, o.order) for o in out]
        want = [(7, 3), (119, 1), (119, 5), (231, 0), (0, 2), (0, 4)]
        record(P + " [" + kind + "]", "Termination", got == want,
               "[231,119,0,7,0,119] -> %s" % [g[0] for g in got])


def test_termination_measures():
    c = OperationCounter()
    ok1, st1 = lps_measure_trace("ABABCABAB")
    record("Proses 1 - Tabel LPS (KMP)", "Batas bawah", ok1, "M=2(m-i)+length >= 0 selama %d iterasi" % st1)
    record("Proses 1 - Tabel LPS (KMP)", "Kemajuan", ok1, "M menurun tegas pada setiap iterasi")
    ok2, st2 = search_measure_trace("ABABABCABABABAB", "ABABAC")
    ok3, st3 = search_measure_trace("AAAAAAAAAAAAAAB", "AAAAB")
    record("Proses 2 - Pencarian KMP", "Batas bawah", ok2 and ok3, "M=(n-i)+(n-s) >= 0 (%d, %d iterasi)" % (st2, st3))
    record("Proses 2 - Pencarian KMP", "Kemajuan", ok2 and ok3, "M menurun tegas pada setiap iterasi")
    # Proses 3: urutan indeks baris yang diproses diukur langsung
    lines = ["a", "b", "ab", "ba", "xab", "q"]
    n = len(lines)
    for kind in ("iter", "rec"):
        sc = LogScanner(["ab"], c, kind == "rec")
        visited = []
        original = sc._check_line

        def spy(ls, idx, original=original, visited=visited):
            visited.append(idx)
            original(ls, idx)
        sc._check_line = spy
        sc.scan(lines)
        once = True
        seen = [0] * n
        for idx in visited:
            if idx < 0 or idx >= n:
                once = False
            else:
                seen[idx] += 1
        for v in seen:
            if v != 1:
                once = False
        asc = True
        for k in range(len(visited) - 1):
            if visited[k] >= visited[k + 1]:
                asc = False
        record("Proses 3 - Pemindaian log [%s]" % kind, "Batas bawah",
               once and sc.results[0].frequency == 2,
               "semua %d indeks 0..n-1 diproses tepat sekali, tak ada di luar rentang" % n)
        record("Proses 3 - Pemindaian log [%s]" % kind, "Kemajuan", asc,
               "urutan indeks %s naik tegas (rentang hi-lo membelah dua pada versi rekursif)" % visited)
    # Proses 4: setiap merge mengurangi jumlah run (n -> n-1 merge)
    rng = random.Random(5)
    ok4 = True
    for _ in range(100):
        k = rng.randrange(1, 30)
        freqs = []
        for _ in range(k):
            freqs.append(rng.randrange(0, 5))
        s = MergeSorter()
        merges = [0]
        orig_merge = s.merge

        def spy_merge(a, b, orig_merge=orig_merge, merges=merges):
            merges[0] += 1
            return orig_merge(a, b)
        s.merge = spy_merge
        out = s.sort_iterative(make_items(freqs))
        if merges[0] != k - 1 or len(out) != k:
            ok4 = False
    record("Proses 4 - Merge Sort", "Batas bawah", ok4, "jumlah run selalu >= 1; hasil akhir 1 run berisi n elemen")
    record("Proses 4 - Merge Sort", "Kemajuan", ok4, "100 daftar acak: tepat n-1 merge, tiap merge mengurangi jumlah run 1")


def main():
    test_lps()
    test_search()
    test_scan()
    test_sort()
    test_termination_measures()
    gagal = 0
    for r in RESULTS:
        if not r[2]:
            gagal += 1
    print("\nTotal pemeriksaan: %d, gagal: %d" % (len(RESULTS), gagal))
    if gagal:
        sys.exit(1)


if __name__ == "__main__":
    main()
