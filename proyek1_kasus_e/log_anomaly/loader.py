"""Pemuat berkas log server."""
import os


class LogLoader:
    """Membaca berkas log dan memecahnya menjadi baris (pemisah '\\n')."""

    def __init__(self, path):
        self.path = path
        self.size_bytes = os.path.getsize(path)

    def load(self):
        with open(self.path, "r", encoding="utf-8", newline="") as f:
            text = f.read()
        lines = text.split("\n")
        if len(lines) > 0 and lines[len(lines) - 1] == "":
            lines.pop()                      # buang elemen kosong setelah newline terakhir
        return lines
