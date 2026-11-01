"""Pemindai log: menjalankan KMP pada setiap baris untuk setiap pola."""
from .kmp import KMPMatcher
from .models import AnomalyResult


class LogScanner:
    """Mengumpulkan frekuensi dan indeks baris pertama tiap pola anomali.

    Frekuensi = jumlah baris log yang mengandung pola (tanpa Counter).
    """

    def __init__(self, patterns, counter, recursive=False):
        self.counter = counter
        self.recursive = recursive
        self.matchers = []
        self.results = []
        for k in range(len(patterns)):
            matcher = KMPMatcher(patterns[k], counter)
            if recursive:
                matcher.build_lps_recursive()
            else:
                matcher.build_lps_iterative()
            self.matchers.append(matcher)
            self.results.append(AnomalyResult(patterns[k], k))

    def _check_line(self, lines, idx):
        line = lines[idx]
        for k in range(len(self.matchers)):
            if self.recursive:
                pos = self.matchers[k].search_recursive(line)
            else:
                pos = self.matchers[k].search_iterative(line)
            if pos != -1:
                res = self.results[k]
                res.frequency += 1
                if res.first_line == -1:
                    res.first_line = idx + 1
                    # (baris diproses berurutan, jadi kemunculan pertama = terkecil)

    # Proses 3: pemindaian seluruh baris (single pass terhadap log)
    def scan_iterative(self, lines):
        for idx in range(len(lines)):
            self._check_line(lines, idx)
        return self.results

    def scan_recursive(self, lines):
        self._scan_range(lines, 0, len(lines))
        return self.results

    def _scan_range(self, lines, lo, hi):
        """Divide and conquer: kedalaman rekursi O(log n)."""
        if hi - lo <= 0:
            return
        if hi - lo == 1:
            self._check_line(lines, lo)
            return
        mid = (lo + hi) // 2
        self._scan_range(lines, lo, mid)     # kiri dulu -> indeks pertama tetap terkecil
        self._scan_range(lines, mid, hi)

    def scan(self, lines):
        if self.recursive:
            return self.scan_recursive(lines)
        return self.scan_iterative(lines)
