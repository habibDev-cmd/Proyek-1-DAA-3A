"""Pipeline utama: muat log -> KMP -> Merge Sort -> laporan."""
from .counter import OperationCounter
from .scanner import LogScanner
from .sorter import MergeSorter
from .report import AnomalyReport


class AnomalyPipeline:
    def __init__(self, patterns, recursive=False):
        self.patterns = patterns
        self.recursive = recursive
        self.counter = OperationCounter()
        self.sorter = MergeSorter()
        self.report = AnomalyReport()
        self.sorted_results = []

    def run(self, lines):
        scanner = LogScanner(self.patterns, self.counter, self.recursive)
        results = scanner.scan(lines)
        if self.recursive:
            self.sorted_results = self.sorter.sort_recursive(results)
        else:
            self.sorted_results = self.sorter.sort_iterative(results)
        return self.sorted_results

    def render(self):
        return self.report.render(self.sorted_results, self.counter.count,
                                  self.sorter.comparisons)
