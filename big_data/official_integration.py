"""Integrate REAL official sources into the warehouse (second + third source).

Sources (acquired by collect_official.py, hash-addressed, with manifests):
  * OBMigra/MJSP "Dados Consolidados da Imigracao no Brasil 2025" (PDF).
    Its tables and charts are images; the only machine-readable figures are the
    ones stated in the report text. Each indicator below is extracted from the
    PDF text layer with an anchored regex on a fixed page and fails loudly if
    the wording changes. Nothing is typed by hand, OCR'd or estimated.
    Reuse basis: p.4 of the report permits reproduction of the text and data
    with source citation, non-commercial. Raw PDF is never redistributed.
  * IBGE Localidades API, municipalities of Sao Paulo (territorial dimension).

These are NATIONAL/STATE reference figures. They are stored next to the
synthetic demand/services gold, never summed into it, and are flagged
synthetic=false. They do not describe Acolhe users.
"""
import argparse, csv, hashlib, json, re, sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

CITATION = ('CAVALCANTI, L; OLIVEIRA, T. Dados Consolidados da Imigracao no Brasil 2025. '
            'Serie Migracoes. OBMigra/MJSP. Brasilia, DF: OBMigra, 2026. ISSN 2448-1076')
NUM = r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?)'
# (indicator_id, page, regex with one numeric group, unit, multiplier, territory, label_pt)
INDICATORS = [
    ('refugee_requests_total', 16, r'totalizou\s+' + NUM + r'\s+mil\s+pedidos', 'persons', 1000, 'BR',
     'Solicitacoes de reconhecimento da condicao de refugiado'),
    ('refugee_requests_change_pct', 16, r'mil\s+pedidos,\s+experimentou\s+aumento\s+de\s+' + NUM + r'%', 'percent', 1, 'BR',
     'Variacao das solicitacoes de refugio vs 2024'),
    ('refugee_requests_children_0_11_pct', 17, r'crian\w+\s+entre\s+0\s+e\s+11\s+anos\s+de\s+idade\s+\(' + NUM + r'%\)', 'percent', 1, 'BR',
     'Participacao de criancas 0-11 anos entre solicitantes de refugio'),
    ('refugee_requests_sp_change_pct', 17, r'S\w+o\s+Paulo/SP\s+surge.*?anterior\s+\((-?' + NUM[1:-1] + r')%\)', 'percent', 1, 'SP',
     'Variacao das solicitacoes de refugio em Sao Paulo/SP vs 2024'),
    ('refugee_recognized_total', 19, r'Solicita\w+\s+deferidas\s+no\s+ano\s+foram\s+' + NUM + r'\s+mil', 'persons', 1000, 'BR',
     'Solicitacoes de refugio deferidas'),
    ('refugee_recognized_children_0_11_pct', 20, r'crian\w+\s+entre\s+0\s+e\s+11\s+anos\s+de\s+idade,\s+cuja\s+participa\w+\s+foi\s+de\s+' + NUM + r'%', 'percent', 1, 'BR',
     'Participacao de criancas 0-11 anos entre refugiados reconhecidos'),
    ('residence_regularized_total', 12, r'foram\s+regularizados\s+' + NUM + r'\s+mil', 'persons', 1000, 'BR',
     'Imigrantes regularizados (registros de residencia)'),
]

def _to_float(text):
    return float(text.replace('.', '').replace(',', '.'))

def latest_raw(root, source_id, extension):
    """Return (path, manifest) of the newest collected snapshot for a source."""
    manifests = sorted((Path(root) / 'manifests').glob(f'*_{source_id}.json'))
    if not manifests: raise FileNotFoundError(f'No manifest for {source_id}; run big_data.collect_official first')
    manifest = json.loads(manifests[-1].read_text(encoding='utf-8'))
    path = Path(root) / manifest['raw_path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['sha256']: raise ValueError(f'Hash mismatch for {path}')
    days = sorted({json.loads(m.read_text(encoding='utf-8'))['retrieval_day_utc'] for m in manifests})
    return path, manifest, days

def extract_obmigra(pdf_path, page_text=None):
    """Extract INDICATORS from the PDF text layer. page_text(n)->str is injectable for tests."""
    if page_text is None:
        try: import pymupdf  # optional dependency, only needed for real extraction
        except ModuleNotFoundError as error:
            raise ModuleNotFoundError('PDF extraction needs PyMuPDF: pip install -r big_data/requirements-official.txt') from error
        doc = pymupdf.open(pdf_path)
        page_text = lambda n: doc[n - 1].get_text()
    rows = []
    for ind_id, page, pattern, unit, mult, territory, label in INDICATORS:
        text = ' '.join(page_text(page).split())
        match = re.search(pattern, text)
        if not match: raise ValueError(f'Indicator {ind_id} not found on page {page}; report wording changed')
        start = max(0, match.start() - 40)
        rows.append({'indicator_id': ind_id, 'value': round(_to_float(match.group(1)) * mult, 4), 'unit': unit,
                     'reference_year': 2025, 'territory': territory, 'label_pt': label, 'page': page,
                     'evidence': text[start:match.end()][:200]})
    return rows

def read_ibge(root):
    path, manifest, days = latest_raw(root, 'ibge_municipalities_sp', 'json')
    folder = Path(root) / 'normalized' / manifest['retrieval_day_utc']
    with (folder / 'municipalities_sp.csv').open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f)), manifest, days

def integrate(official_root, output_dir, page_text=None):
    official_root = Path(official_root); output_dir = Path(output_dir)
    pdf, ob_manifest, ob_days = latest_raw(official_root, 'obmigra_consolidated_2025', 'pdf')
    indicators = extract_obmigra(pdf, page_text)
    municipalities, ibge_manifest, ibge_days = read_ibge(official_root)
    with closing(sqlite3.connect(output_dir / 'warehouse.db')) as db, db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS official_batches (source TEXT, sha256 TEXT, retrieval_day_utc TEXT, records INTEGER, integrated_at TEXT, PRIMARY KEY(source, sha256, retrieval_day_utc));
        CREATE TABLE IF NOT EXISTS silver_official_indicator (indicator_id TEXT, reference_year INTEGER, territory TEXT, value REAL, unit TEXT, label_pt TEXT, page INTEGER, evidence TEXT, source_sha256 TEXT, PRIMARY KEY(indicator_id, reference_year, territory));
        CREATE TABLE IF NOT EXISTS dim_municipality (municipality_id INTEGER PRIMARY KEY, municipality TEXT NOT NULL, state_code TEXT NOT NULL, state TEXT NOT NULL, source_sha256 TEXT);
        """)
        now = datetime.now(timezone.utc).isoformat()
        for r in indicators:
            db.execute("""INSERT INTO silver_official_indicator VALUES(?,?,?,?,?,?,?,?,?)
              ON CONFLICT(indicator_id, reference_year, territory) DO UPDATE SET value=excluded.value, unit=excluded.unit,
              label_pt=excluded.label_pt, page=excluded.page, evidence=excluded.evidence, source_sha256=excluded.source_sha256""",
              (r['indicator_id'], r['reference_year'], r['territory'], r['value'], r['unit'], r['label_pt'], r['page'], r['evidence'], ob_manifest['sha256']))
        for m in municipalities:
            db.execute("""INSERT INTO dim_municipality VALUES(?,?,?,?,?) ON CONFLICT(municipality_id) DO UPDATE SET
              municipality=excluded.municipality, state_code=excluded.state_code, state=excluded.state, source_sha256=excluded.source_sha256""",
              (int(m['municipality_id']), m['municipality'], m['state_code'], m['state'], ibge_manifest['sha256']))
        for src, man, n in (('obmigra', ob_manifest, len(indicators)), ('ibge', ibge_manifest, len(municipalities))):
            db.execute('INSERT OR IGNORE INTO official_batches VALUES(?,?,?,?,?)', (src, man['sha256'], man['retrieval_day_utc'], n, now))
        db.executescript("""
        DROP TABLE IF EXISTS gold_official_context;
        CREATE TABLE gold_official_context AS
          SELECT indicator_id, reference_year, territory, value, unit, label_pt, page FROM silver_official_indicator;
        """)
        counts = {t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                  for t in ('silver_official_indicator', 'dim_municipality', 'official_batches', 'gold_official_context')}
        sp_count = db.execute("SELECT COUNT(*) FROM dim_municipality WHERE state_code='SP'").fetchone()[0]
        gold = [dict(zip(('indicator_id', 'reference_year', 'territory', 'value', 'unit', 'label_pt', 'page'), row))
                for row in db.execute('SELECT * FROM gold_official_context ORDER BY indicator_id')]
    context = {'synthetic': False, 'reference_year': 2025, 'indicators': gold,
               'territory': {'state_code': 'SP', 'municipalities': sp_count},
               'provenance': {'obmigra': {'citation': CITATION, 'sha256': ob_manifest['sha256'], 'retrieval_days_utc': ob_days, 'url': ob_manifest['url']},
                              'ibge': {'sha256': ibge_manifest['sha256'], 'retrieval_days_utc': ibge_days, 'url': ibge_manifest['url']}},
               'note': 'Indicadores oficiais nacionais/estaduais de contexto; nao descrevem usuarios do Acolhe e nao sao somados a camada sintetica.'}
    summary_path = output_dir / 'summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    summary['official_context'] = context
    tmp = output_dir / 'summary.tmp'; tmp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'); tmp.replace(summary_path)
    with (output_dir / 'gold_official_context.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(gold[0])); w.writeheader(); w.writerows(gold)
    return {'counts': counts, 'official_context': context}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--official', default='big_data/official_snapshots'); p.add_argument('--output', default='big_data/output')
    a = p.parse_args()
    print(json.dumps(integrate(a.official, a.output), ensure_ascii=False, indent=2))
