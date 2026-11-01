"""Model data hasil pemindaian."""


class AnomalyResult:
    """Hasil satu pola anomali: frekuensi baris dan indeks baris pertama."""

    def __init__(self, pattern, order):
        self.pattern = pattern
        self.order = order          # urutan asli pola (untuk stabilitas)
        self.frequency = 0          # jumlah baris log yang mengandung pola
        self.first_line = -1        # nomor baris pertama (mulai dari 1), -1 = tidak ada

    def __repr__(self):
        return "AnomalyResult(%r, freq=%d, first=%d)" % (
            self.pattern, self.frequency, self.first_line)
