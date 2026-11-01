"""Pembuat laporan anomali sesuai format contoh soal."""


class AnomalyReport:
    HEADER = "=== LAPORAN ANOMALI LOG SERVER (TERURUT DARI PALING LANGKA) ==="

    def render(self, results, char_ops, sort_comparisons=None):
        out = [self.HEADER]
        for k in range(len(results)):
            r = results[k]
            first = "-" if r.first_line == -1 else str(r.first_line)
            out.append('%d. Pola: "%s"' % (k + 1, r.pattern))
            out.append("   Indeks Pertama: %s" % first)
            out.append("   Frekuensi: %d" % r.frequency)
        out.append("Metrik Eksekusi:")
        out.append("- Total Operasi Dasar (Perbandingan Karakter): %d operasi" % char_ops)
        if sort_comparisons is not None:
            out.append("- Perbandingan pada Pengurutan (Merge Sort): %d operasi" % sort_comparisons)
        return "\n".join(out)
