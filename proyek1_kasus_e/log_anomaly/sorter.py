"""Merge Sort stabil: versi rekursif (top-down) dan iteratif (bottom-up).

Tidak memakai sorted() maupun list.sort().
Urutan: pola yang ditemukan dari frekuensi terkecil (paling langka);
pola dengan frekuensi 0 (tidak ditemukan) ditaruh paling akhir.
"""


class MergeSorter:
    def __init__(self):
        self.comparisons = 0

    def less_equal(self, a, b):
        """True jika a harus berada sebelum atau sama dengan b."""
        self.comparisons += 1
        a_missing = 1 if a.frequency == 0 else 0
        b_missing = 1 if b.frequency == 0 else 0
        if a_missing != b_missing:
            return a_missing < b_missing
        if a.frequency != b.frequency:
            return a.frequency < b.frequency
        return a.order <= b.order            # stabil

    def merge(self, left, right):
        out = []
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if self.less_equal(left[i], right[j]):
                out.append(left[i])
                i += 1
            else:
                out.append(right[j])
                j += 1
        while i < len(left):
            out.append(left[i])
            i += 1
        while j < len(right):
            out.append(right[j])
            j += 1
        return out

    # Proses 4a: rekursif (top-down)
    def sort_recursive(self, items):
        n = len(items)
        if n <= 1:                           # basis
            return items[:]
        mid = n // 2
        left = self.sort_recursive(items[:mid])
        right = self.sort_recursive(items[mid:])
        return self.merge(left, right)

    # Proses 4b: iteratif (bottom-up)
    def sort_iterative(self, items):
        n = len(items)
        runs = []
        for k in range(n):
            runs.append([items[k]])          # n run berukuran 1
        while len(runs) > 1:
            merged = []
            k = 0
            while k + 1 < len(runs):
                merged.append(self.merge(runs[k], runs[k + 1]))
                k += 2
            if k < len(runs):
                merged.append(runs[k])
            runs = merged
        if len(runs) == 0:
            return []
        return runs[0]
