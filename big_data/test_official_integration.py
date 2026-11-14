from contextlib import closing
import csv, json, re, sqlite3, tempfile, unittest
from pathlib import Path
from big_data.collect_official import save_snapshot
from big_data.official_integration import extract_obmigra, integrate, INDICATORS
from big_data.pipeline import create_demo, run

# Sentences in the exact wording of the OBMigra 2025 report text layer.
PAGES = {
    12: 'ao todo foram regularizados 199,6 mil imigrantes',
    16: 'o volume de solicitação, que totalizou 75,6 mil pedidos, experimentou aumento de 10,9% (Gráfico 7).',
    17: 'São Paulo/SP surge na quarta posição, mas com variação levemente negativa na comparação com o ano anterior (-2,5%). '
        'diminuiu a contribuição de crianças entre 0 e 11 anos de idade (16,0%).',
    19: 'Solicitações deferidas no ano foram 9,2 mil3.',
    20: 'participação das crianças entre 0 e 11 anos de idade, cuja participação foi de 24,4%, se constituindo',
}

def fake_snapshots(root):
    """Build a hash-addressed snapshot tree like collect_official.py produces."""
    ibge = save_snapshot(root, {'id': 'ibge_municipalities_sp', 'url': 'https://example/ibge', 'extension': 'json'}, b'[]', {'status': 200})
    folder = Path(root) / 'normalized' / ibge['retrieval_day_utc']; folder.mkdir(parents=True)
    with (folder / 'municipalities_sp.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['municipality_id', 'municipality', 'state_id', 'state_code', 'state'])
        w.writerow([3500105, 'Adamantina', 35, 'SP', 'Sao Paulo']); w.writerow([3550308, 'Sao Paulo', 35, 'SP', 'Sao Paulo'])
    save_snapshot(root, {'id': 'obmigra_consolidated_2025', 'url': 'https://example/obmigra.pdf', 'extension': 'pdf'}, b'%PDF-fake', {'status': 200})

class OfficialIntegrationTests(unittest.TestCase):
    def test_extracts_every_indicator_from_text(self):
        rows = {r['indicator_id']: r for r in extract_obmigra(None, lambda n: PAGES.get(n, ''))}
        self.assertEqual(set(rows), {i[0] for i in INDICATORS})
        self.assertEqual(rows['refugee_requests_total']['value'], 75600)
        self.assertEqual(rows['refugee_requests_children_0_11_pct']['value'], 16.0)
        self.assertEqual(rows['refugee_requests_sp_change_pct']['value'], -2.5)
        self.assertEqual(rows['refugee_recognized_total']['value'], 9200)
        self.assertTrue(all(r['page'] and r['evidence'] for r in rows.values()))

    def test_changed_wording_fails_loudly(self):
        pages = {**PAGES, 16: 'texto diferente'}
        with self.assertRaisesRegex(ValueError, 'refugee_requests_total'):
            extract_obmigra(None, lambda n: pages.get(n, ''))

    def test_integration_idempotent_and_kept_apart_from_synthetic(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); create_demo(p / 'input'); run(p / 'input', p / 'output'); fake_snapshots(p / 'snap')
            first = integrate(p / 'snap', p / 'output', lambda n: PAGES.get(n, ''))
            second = integrate(p / 'snap', p / 'output', lambda n: PAGES.get(n, ''))
            self.assertEqual(first['counts'], second['counts'])
            self.assertEqual(first['counts']['silver_official_indicator'], len(INDICATORS))
            self.assertEqual(first['counts']['dim_municipality'], 2)
            self.assertEqual(first['counts']['official_batches'], 2)
            summary = json.loads((p / 'output' / 'summary.json').read_text(encoding='utf-8'))
            self.assertTrue(summary['synthetic'])                       # demo demand/services stay flagged
            self.assertFalse(summary['official_context']['synthetic'])  # official context is real
            self.assertEqual(summary['totals']['demand'], 190)          # official data never summed in
            # All eight gold queries, synthetic and official, return rows.
            sql = re.sub(r'--[^\n]*', '', Path(__file__).with_name('queries.sql').read_text(encoding='utf-8'))
            statements = [s for s in sql.split(';') if s.strip()]
            self.assertEqual(len(statements), 8)
            with closing(sqlite3.connect(p / 'output' / 'warehouse.db')) as db:
                for s in statements: self.assertTrue(db.execute(s).fetchall(), s)
                self.assertEqual(db.execute(statements[5]).fetchone()[2], 12096)  # 75600 * 16%

    def test_tampered_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); fake_snapshots(p / 'snap')
            pdf = next((p / 'snap' / 'raw' / 'obmigra_consolidated_2025').glob('*.pdf')); pdf.write_bytes(b'%PDF-tampered')
            with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
                integrate(p / 'snap', p / 'output', lambda n: PAGES.get(n, ''))
