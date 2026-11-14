import tempfile, unittest
from pathlib import Path
from big_data.evidence import build, render, TABLES
from big_data.pipeline import create_demo

class EvidenceTests(unittest.TestCase):
    def test_counts_per_batch_and_rerun_without_official(self):
        with tempfile.TemporaryDirectory() as d:
            create_demo(Path(d) / 'in')
            rows, official, queries, _ = build(Path(d) / 'no_official', Path(d) / 'in')
            counts = {name: [c[t] for t in TABLES] for name, c in rows}
            self.assertEqual(counts['Depois do lote 2026-11-05'], [2, 4, 4, 0, 4])
            self.assertEqual(counts['Depois do lote 2026-11-06'], [4, 8, 4, 0, 4])
            self.assertEqual(counts['Reexecucao (mesmos arquivos)'], counts['Depois do lote 2026-11-06'])
            self.assertEqual(official, [])
            self.assertTrue(all(err is None for *_, err in queries[:5]))  # synthetic gold queries
            self.assertTrue(all(err for *_, err in queries[5:]))           # official tables absent -> reported, not hidden
            self.assertIn('Consulta 8', render(rows, official, queries, _))
