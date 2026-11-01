"""Penghitung operasi dasar (perbandingan karakter)."""


class OperationCounter:
    """Menghitung jumlah perbandingan karakter yang dilakukan algoritma."""

    def __init__(self):
        self.count = 0

    def tick(self, n=1):
        self.count += n

    def reset(self):
        self.count = 0
