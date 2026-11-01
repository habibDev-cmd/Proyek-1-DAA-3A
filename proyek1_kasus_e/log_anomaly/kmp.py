"""Algoritma Knuth-Morris-Pratt (KMP): versi iteratif dan rekursif."""


class KMPMatcher:
    """Pencocok pola tunggal dengan KMP.

    Setiap perbandingan karakter dicatat ke OperationCounter.
    Tidak memakai `in`, str.find(), str.index(), re, maupun Counter.
    """

    def __init__(self, pattern, counter):
        if len(pattern) == 0:
            raise ValueError("pola tidak boleh kosong")
        self.pattern = pattern
        self.m = len(pattern)
        self.counter = counter
        self.lps = None

    # ------------------------------------------------------------------
    # Proses 1: tabel LPS (longest proper prefix yang juga suffix)
    # ------------------------------------------------------------------
    def build_lps_iterative(self):
        p, m = self.pattern, self.m
        lps = [0] * m
        length = 0
        i = 1
        while i < m:
            self.counter.tick()
            if p[i] == p[length]:
                length += 1
                lps[i] = length
                i += 1
            elif length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
        self.lps = lps
        return lps

    def build_lps_recursive(self):
        lps = [0] * self.m
        self._lps_rec(1, 0, lps)
        self.lps = lps
        return lps

    def _lps_rec(self, i, length, lps):
        if i >= self.m:                      # basis: seluruh pola terproses
            return
        self.counter.tick()
        if self.pattern[i] == self.pattern[length]:
            lps[i] = length + 1
            self._lps_rec(i + 1, length + 1, lps)
        elif length != 0:
            self._lps_rec(i, lps[length - 1], lps)
        else:
            lps[i] = 0
            self._lps_rec(i + 1, 0, lps)

    # ------------------------------------------------------------------
    # Proses 2: pencarian pola dalam satu baris log
    # Mengembalikan indeks kemunculan pertama, atau -1 bila tidak ada.
    # ------------------------------------------------------------------
    def search_iterative(self, text):
        p, m, lps = self.pattern, self.m, self.lps
        n = len(text)
        i = 0
        j = 0
        while i < n:
            self.counter.tick()
            if text[i] == p[j]:
                i += 1
                j += 1
                if j == m:
                    return i - j
            elif j != 0:
                j = lps[j - 1]
            else:
                i += 1
        return -1

    def search_recursive(self, text):
        return self._search_rec(text, 0, 0)

    def _search_rec(self, text, i, j):
        if i >= len(text):                   # basis: teks habis
            return -1
        self.counter.tick()
        if text[i] == self.pattern[j]:
            if j + 1 == self.m:
                return i + 1 - self.m
            return self._search_rec(text, i + 1, j + 1)
        elif j != 0:
            return self._search_rec(text, i, self.lps[j - 1])
        return self._search_rec(text, i + 1, 0)
